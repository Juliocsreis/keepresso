import Testing
import Foundation
@testable import KeepressoCore

private let t0 = Date(timeIntervalSince1970: 2_000_000)
private let grace: TimeInterval = 300

/// The policy plus the time of its last step, so the helper below can fill in
/// the once-a-second host ticks between the times a test names (a gap longer
/// than ``OfflinePausePolicy/maxStepGap`` means "the Mac slept").
private struct Stepper {
    var policy = OfflinePausePolicy()
    var last: TimeInterval?
    var paused: Bool { policy.paused }
    var wantsProbe: Bool { policy.wantsProbe }
}

/// Step the policy with the lid closed and the override on unless told otherwise.
private func step(
    _ s: inout Stepper,
    at seconds: TimeInterval,
    lid: Bool? = true,
    override: Bool? = true,
    external: Bool? = nil,
    probe: InternetProbeResult? = .offline,
    hotspot: Bool = false,
    fill: Bool = true
) -> OfflineReading {
    if fill, let last = s.last {
        var t = last + 30
        while t < seconds {
            _ = s.policy.step(lidClosed: lid, overrideActive: override, externalDisplay: external, probe: probe,
                              hotspotConnecting: hotspot, graceSeconds: grace, now: t0.addingTimeInterval(t))
            t += 30
        }
    }
    s.last = seconds
    return s.policy.step(lidClosed: lid, overrideActive: override, externalDisplay: external, probe: probe,
                         hotspotConnecting: hotspot, graceSeconds: grace, now: t0.addingTimeInterval(seconds))
}

@Test func offlinePausesOnlyAfterTheGracePeriod() {
    var policy = Stepper()
    #expect(step(&policy, at: 0) == .clear)
    #expect(step(&policy, at: 299) == .clear)
    #expect(step(&policy, at: 300) == .offline)
    #expect(policy.paused)
}

@Test func onlineResetsTheGracePeriod() {
    var policy = Stepper()
    _ = step(&policy, at: 0)
    _ = step(&policy, at: 200)
    #expect(step(&policy, at: 210, probe: .online) == .clear)
    #expect(step(&policy, at: 220) == .clear)
    #expect(step(&policy, at: 510) == .clear)   // 290 s since it went offline again
    #expect(step(&policy, at: 520) == .offline)
}

@Test func noProbeResultNeverAdvancesTheGracePeriod() {
    var policy = Stepper()
    #expect(step(&policy, at: 0, probe: nil) == .clear)
    #expect(step(&policy, at: 1000, probe: nil) == .clear)
    #expect(step(&policy, at: 1010) == .clear)  // first offline result starts the clock
    #expect(step(&policy, at: 1310) == .offline)
}

@Test func hotspotConnectionInProgressHoldsThePause() {
    var policy = Stepper()
    _ = step(&policy, at: 0)
    #expect(step(&policy, at: 400, hotspot: true) == .clear)
    #expect(step(&policy, at: 405) == .offline)
}

@Test func notArmedWithoutTheSleepOverride() {
    var policy = Stepper()
    #expect(step(&policy, at: 0, override: false) == .clear)
    #expect(step(&policy, at: 1000, override: false) == .clear)
    #expect(policy.wantsProbe == false)
}

@Test func lidOpenNeverArms() {
    var policy = Stepper()
    #expect(step(&policy, at: 0, lid: false) == .clear)
    #expect(step(&policy, at: 1000, lid: false) == .clear)
    #expect(policy.wantsProbe == false)
}

@Test func pauseSurvivesTheOverrideDropping() {
    // The pause itself switches closed-display off. That must not clear it,
    // or the session restarts and holds an offline Mac awake in a loop.
    var policy = Stepper()
    _ = step(&policy, at: 0)
    #expect(step(&policy, at: 300) == .offline)
    #expect(step(&policy, at: 301, override: false) == .offline)
    #expect(step(&policy, at: 900, override: false) == .offline)
    #expect(policy.wantsProbe)  // keeps checking so internet coming back can resume
}

@Test func lidOpeningClearsThePause() {
    var policy = Stepper()
    _ = step(&policy, at: 0)
    _ = step(&policy, at: 300)
    #expect(step(&policy, at: 310, lid: false, override: false) == .clear)
    #expect(policy.paused == false)
}

@Test func internetComingBackClearsThePause() {
    var policy = Stepper()
    _ = step(&policy, at: 0)
    _ = step(&policy, at: 300)
    #expect(step(&policy, at: 320, override: false, probe: .online) == .clear)
    #expect(policy.paused == false)
}

@Test func unreadableLidAndOverrideKeepTheirLastValues() {
    var policy = Stepper()
    _ = step(&policy, at: 0)
    #expect(step(&policy, at: 300, lid: nil, override: nil) == .offline)
}

@Test func graceMinutesSnapToTheOfferedChoices() {
    #expect(OfflinePausePolicy.clampedGraceMinutes(1) == 3)
    #expect(OfflinePausePolicy.clampedGraceMinutes(5) == 5)
    #expect(OfflinePausePolicy.clampedGraceMinutes(7) == 5)
    #expect(OfflinePausePolicy.clampedGraceMinutes(8) == 10)
    #expect(OfflinePausePolicy.clampedGraceMinutes(999) == 30)
}

@Test func settingsRoundTripTheGracePeriod() throws {
    var settings = KeepressoSettings()
    settings.pauseWhenOfflineMinutes = 10
    let data = try JSONEncoder().encode(settings)
    let decoded = try JSONDecoder().decode(KeepressoSettings.self, from: data)
    #expect(decoded.pauseWhenOfflineMinutes == 10)
    #expect(KeepressoSettings().pauseWhenOfflineMinutes == nil)
}

// MARK: - Controller

private final class FakeProbe: InternetProbing, @unchecked Sendable {
    private let lock = NSLock()
    private var _result: InternetProbeResult = .offline
    private var _calls = 0
    var result: InternetProbeResult {
        get { lock.withLock { _result } }
        set { lock.withLock { _result = newValue } }
    }
    var calls: Int { lock.withLock { _calls } }
    func probe() -> InternetProbeResult {
        lock.withLock { _calls += 1; return _result }
    }
}

@MainActor
@Test func controllerProbesOnlyWhileWatchingAndPauses() async {
    let probe = FakeProbe()
    let controller = OfflinePauseController(probe: probe)
    controller.graceMinutes = 3

    // Lid open: no probing at all.
    controller.tick(lidClosed: false, overrideActive: true, hotspotConnecting: false, now: t0)
    await controller.settleProbe()
    #expect(probe.calls == 0)

    // Lid closed with the override: probes, then pauses after the grace.
    controller.tick(lidClosed: true, overrideActive: true, hotspotConnecting: false, now: t0)
    await controller.settleProbe()
    #expect(probe.calls == 1)
    #expect(controller.tick(lidClosed: true, overrideActive: true, hotspotConnecting: false,
                            now: t0.addingTimeInterval(1)) == .clear)
    // Tick every 20 s, the way fresh checks arrive, until the grace runs out.
    var now = t0.addingTimeInterval(1)
    var verdict = OfflineReading.clear
    while verdict == .clear, now < t0.addingTimeInterval(400) {
        await controller.settleProbe()
        now.addTimeInterval(20)
        verdict = controller.tick(lidClosed: true, overrideActive: true, hotspotConnecting: false, now: now)
    }
    #expect(verdict == .offline)
    #expect(now.timeIntervalSince(t0) >= 180)
    // The pause drops the override; it stays paused.
    #expect(controller.tick(lidClosed: true, overrideActive: false, hotspotConnecting: false,
                            now: now.addingTimeInterval(1)) == .offline)

    // Internet back: the next check clears it.
    probe.result = .online
    await controller.settleProbe()
    controller.tick(lidClosed: true, overrideActive: false, hotspotConnecting: false,
                    now: now.addingTimeInterval(21))
    await controller.settleProbe()
    #expect(controller.tick(lidClosed: true, overrideActive: false, hotspotConnecting: false,
                            now: now.addingTimeInterval(22)) == .clear)
}

@MainActor
@Test func controllerOffReportsUnknown() {
    let controller = OfflinePauseController(probe: FakeProbe())
    #expect(controller.tick(lidClosed: true, overrideActive: true, hotspotConnecting: false) == .unknown)
}

// MARK: - External display, stale checks, grace changes

@Test func externalDisplayNeverArms() {
    var policy = Stepper()
    #expect(step(&policy, at: 0, external: true) == .clear)
    #expect(step(&policy, at: 400) == .clear)
    #expect(policy.wantsProbe == false)
}

@Test func attachingAnExternalDisplayClearsThePause() {
    var policy = Stepper()
    _ = step(&policy, at: 0)
    #expect(step(&policy, at: 300) == .offline)
    #expect(step(&policy, at: 301, override: false, external: true) == .clear)
    #expect(policy.paused == false)
}

@Test func aLongGapBetweenStepsRestartsTheGracePeriod() {
    var policy = Stepper()
    _ = step(&policy, at: 0)
    _ = step(&policy, at: 30)
    // The Mac slept for an hour: the offline time before doesn't count.
    #expect(step(&policy, at: 3630, fill: false) == .clear)
    #expect(step(&policy, at: 3900) == .clear)
    #expect(step(&policy, at: 3930) == .offline)
}

@MainActor
@Test func controllerIgnoresAStaleCheckAfterWake() async {
    let probe = FakeProbe()
    let controller = OfflinePauseController(probe: probe)
    controller.graceMinutes = 3
    controller.tick(lidClosed: true, overrideActive: true, hotspotConnecting: false, now: t0)
    await controller.settleProbe()
    controller.tick(lidClosed: true, overrideActive: true, hotspotConnecting: false, now: t0.addingTimeInterval(1))

    // Wakes two hours later on a working network. The old offline result is
    // stale and must not pause before the fresh check comes back.
    probe.result = .online
    let wake = t0.addingTimeInterval(7200)
    #expect(controller.tick(lidClosed: true, overrideActive: true, hotspotConnecting: false, now: wake) == .clear)
    await controller.settleProbe()
    #expect(controller.tick(lidClosed: true, overrideActive: true, hotspotConnecting: false,
                            now: wake.addingTimeInterval(1)) == .clear)
    #expect(controller.isPaused == false)
}

@MainActor
@Test func changingTheGracePeriodKeepsALatchedPause() async {
    let probe = FakeProbe()
    let controller = OfflinePauseController(probe: probe)
    controller.graceMinutes = 3
    var now = t0
    controller.tick(lidClosed: true, overrideActive: true, hotspotConnecting: false, now: now)
    // Keep checks fresh while the grace period runs out.
    while !controller.isPaused {
        await controller.settleProbe()
        now.addTimeInterval(20)
        controller.tick(lidClosed: true, overrideActive: true, hotspotConnecting: false, now: now)
    }
    controller.graceMinutes = 10
    #expect(controller.isPaused)
    await controller.settleProbe()
    #expect(controller.tick(lidClosed: true, overrideActive: false, hotspotConnecting: false,
                            now: now.addingTimeInterval(1)) == .offline)
    // Switching the feature off and on does start over.
    controller.graceMinutes = nil
    controller.graceMinutes = 10
    #expect(controller.isPaused == false)
}
