import Foundation

/// One internet check. A captive-portal login page counts as offline: the
/// Mac has a network but nothing it runs can reach the internet through it.
public enum InternetProbeResult: Equatable, Sendable {
    case online
    case offline
}

/// The offline guard's verdict, latched by ``SessionController`` the same way
/// as ``ThermalReading``: `.offline` stops and holds, `.clear` releases, and
/// `.unknown` (feature off, or an internal reconcile) leaves the latch alone.
public enum OfflineReading: Equatable, Sendable {
    case offline
    case clear
    case unknown
}

/// Checks whether the internet is actually reachable. Blocking (up to a few
/// seconds), so callers run it off the main actor.
public protocol InternetProbing: Sendable {
    func probe() -> InternetProbeResult
}

/// The real probe: Apple's captive-portal check, the same request macOS and
/// the Public Wi-Fi assistant use. Only Apple's "Success" page means online.
public struct CaptiveInternetProbe: InternetProbing {
    public init() {}

    public func probe() -> InternetProbeResult {
        SystemCaptiveProbe.probeCaptiveHTTP() == .success ? .online : .offline
    }
}

/// Pure decision for "let a lid-closed Mac sleep when it has no internet".
///
/// Arms only with the lid closed, no external display attached (a clamshell
/// Mac driving a monitor is in use as a desktop), and closed-display mode
/// holding the Mac awake. Pauses once every check for the whole grace period
/// has come back offline and no hotspot connection is in progress. Once
/// paused, it stays paused until the lid opens, an external display is
/// attached, or a check comes back online. Nothing else clears it: the pause itself switches closed-display mode off, so clearing
/// on "override no longer active" would restart the session, turn the
/// override back on, and keep an offline Mac awake in a loop.
///
/// Lid and override readings can be `nil` transiently (`AppleClamshellState`
/// flutters, `pmset -g` can fail), so they go through a ``ThermalArming``,
/// which latches each one's last known value.
public struct OfflinePausePolicy: Equatable, Sendable {
    /// Grace periods offered in Preferences, in minutes. The floor (3) is above
    /// the hotspot fallback's longest first-attempt delay (2 minutes), so the
    /// fallback always gets a try before the Mac is allowed to sleep.
    public static let graceMinuteChoices = [3, 5, 10, 15, 30]
    public static let defaultGraceMinutes = 5

    /// Snap any stored value onto the offered choices (nearest, ties upward).
    public static func clampedGraceMinutes(_ raw: Int) -> Int {
        graceMinuteChoices.min { lhs, rhs in
            let l = abs(lhs - raw), r = abs(rhs - raw)
            return l == r ? lhs > rhs : l < r
        } ?? defaultGraceMinutes
    }

    /// A gap between steps longer than this means the host wasn't watching
    /// (the Mac slept), so the grace period starts over.
    public static let maxStepGap: TimeInterval = 60

    private var arming = ThermalArming()
    private var externalDisplay = false
    private var offlineSince: Date?
    private var lastStepAt: Date?
    public private(set) var paused = false

    public init() {}

    /// Whether the host should keep checking the internet this tick.
    public var wantsProbe: Bool {
        arming.latchedLidClosed && !externalDisplay && (arming.latchedOverrideActive || paused)
    }

    /// Fold in this tick's readings and return the verdict for the session.
    ///
    /// - Parameters:
    ///   - externalDisplay: whether an external display is attached; `nil`
    ///     (not read this tick) keeps the last known value.
    ///   - probe: the latest fresh internet check, or `nil` while none is
    ///     available. `nil` never advances the grace period.
    public mutating func step(
        lidClosed: Bool?,
        overrideActive: Bool?,
        externalDisplay: Bool? = nil,
        probe: InternetProbeResult?,
        hotspotConnecting: Bool,
        graceSeconds: TimeInterval,
        now: Date
    ) -> OfflineReading {
        _ = arming.update(lidClosed: lidClosed, sleepOverrideActive: overrideActive)
        if let externalDisplay { self.externalDisplay = externalDisplay }
        if let lastStepAt, now.timeIntervalSince(lastStepAt) > Self.maxStepGap {
            // Slept or otherwise not watching: offline time before the gap
            // doesn't count toward the grace period.
            offlineSince = nil
        }
        lastStepAt = now

        // Opening the lid always ends it: the user is back. So does a lid shut
        // over an external display: the Mac is being used as a desktop.
        guard arming.latchedLidClosed, !self.externalDisplay else {
            reset()
            return .clear
        }
        // Internet came back (while the Mac was still awake): resume.
        if probe == .online {
            reset()
            return .clear
        }
        if paused { return .offline }
        // Not armed: lid closed but nothing is overriding sleep.
        guard arming.latchedOverrideActive else {
            offlineSince = nil
            return .clear
        }
        guard probe == .offline else { return .clear }
        let since = offlineSince ?? now
        offlineSince = since
        guard !hotspotConnecting, now.timeIntervalSince(since) >= graceSeconds else {
            return .clear
        }
        paused = true
        return .offline
    }

    public mutating func reset() {
        paused = false
        offlineSince = nil
    }
}

/// Owns the live offline guard: runs the internet check in the background at
/// most every ``probeInterval`` seconds while the policy wants it, and folds
/// the latest result into ``OfflinePausePolicy`` on each host tick.
@MainActor
public final class OfflinePauseController {
    /// Seconds between internet checks while watching.
    public static let probeInterval: TimeInterval = 20

    /// A check result older than this is ignored (the Mac slept, or a check
    /// is overdue): two intervals plus the probe's own 6 s worst case.
    public static let staleAfter: TimeInterval = probeInterval * 2 + 10

    /// Grace period in minutes; `nil` = feature off. Switching the feature on
    /// or off starts over; a new grace value just applies from the next tick,
    /// so a latched pause survives it.
    public var graceMinutes: Int? {
        didSet {
            guard (graceMinutes == nil) != (oldValue == nil) else { return }
            policy.reset()
            // Also drops an in-flight check, so it can't land on the fresh policy.
            stopProbing()
        }
    }

    /// Whether a pause is latched, so the host keeps reading the lid for it
    /// even after the pause has switched closed-display off.
    public var isPaused: Bool { policy.paused }

    /// The latest internet check while watching, and when it started; `nil`
    /// when not watching.
    private var lastProbe: (result: InternetProbeResult, startedAt: Date)?
    private var policy = OfflinePausePolicy()
    private let prober: InternetProbing
    private var lastProbeAt: Date?
    private var task: Task<Void, Never>?

    public init(probe: InternetProbing = CaptiveInternetProbe()) {
        self.prober = probe
    }

    /// One host tick. Returns the verdict for ``SessionController``.
    @discardableResult
    public func tick(
        lidClosed: Bool?,
        overrideActive: Bool?,
        externalDisplay: Bool? = nil,
        hotspotConnecting: Bool,
        now: Date = Date()
    ) -> OfflineReading {
        guard let graceMinutes else {
            stopProbing()
            return .unknown
        }
        let fresh = lastProbe.flatMap {
            now.timeIntervalSince($0.startedAt) <= Self.staleAfter ? $0.result : nil
        }
        let verdict = policy.step(
            lidClosed: lidClosed,
            overrideActive: overrideActive,
            externalDisplay: externalDisplay,
            probe: fresh,
            hotspotConnecting: hotspotConnecting,
            graceSeconds: TimeInterval(graceMinutes) * 60,
            now: now
        )
        if policy.wantsProbe {
            scheduleProbe(now: now)
        } else {
            // Never carry a stale result into the next time the lid closes.
            stopProbing()
        }
        return verdict
    }

    /// Await the in-flight check, if any. For tests.
    public func settleProbe() async {
        await task?.value
    }

    private func scheduleProbe(now: Date) {
        guard task == nil else { return }
        if let lastProbeAt, now.timeIntervalSince(lastProbeAt) < Self.probeInterval { return }
        lastProbeAt = now
        task = Task { [weak self, prober] in
            // The probe blocks on a semaphore for up to 6 s; keep that off the
            // cooperative pool, which has only about a thread per core.
            let result = await withCheckedContinuation { continuation in
                DispatchQueue.global(qos: .utility).async {
                    continuation.resume(returning: prober.probe())
                }
            }
            guard let self, !Task.isCancelled else { return }
            self.lastProbe = (result, now)
            self.task = nil
        }
    }

    private func stopProbing() {
        task?.cancel()
        task = nil
        lastProbe = nil
        lastProbeAt = nil
    }
}
