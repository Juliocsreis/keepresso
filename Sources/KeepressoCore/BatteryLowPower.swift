import Foundation
import Observation

public enum LowPowerProfile: String, CaseIterable, Sendable {
    case battery, adapter
}

public protocol BatteryLowPowerControlling: Sendable {
    func batteryMode() -> Int?
    func setBatteryMode(_ mode: Int) -> Bool
    func adapterMode() -> Int?
    func setAdapterMode(_ mode: Int) -> Bool
}
public extension BatteryLowPowerControlling {
    func adapterMode() -> Int? { nil }
    func setAdapterMode(_ mode: Int) -> Bool { false }
    func mode(for profile: LowPowerProfile) -> Int? {
        profile == .battery ? batteryMode() : adapterMode()
    }
    func setMode(_ mode: Int, for profile: LowPowerProfile) -> Bool {
        profile == .battery ? setBatteryMode(mode) : setAdapterMode(mode)
    }
}
public struct PMSetBatteryLowPowerControl: BatteryLowPowerControlling {
    private let runner: HelperCommandRunning
    private let readOutput: @Sendable () -> String?
    public init(runner: HelperCommandRunning = ProcessCommandRunner(),
                readOutput: @escaping @Sendable () -> String? = { PMSetBatteryLowPowerControl.readSettingsOutput() }) {
        self.runner = runner; self.readOutput = readOutput
    }
    public func batteryMode() -> Int? { settings(for: .battery)?.mode }
    public func adapterMode() -> Int? { settings(for: .adapter)?.mode }
    private func settings(for profile: LowPowerProfile) -> (key: String, mode: Int, hasHighPower: Bool)? {
        guard let output = readOutput() else { return nil }
        return Self.parseSettings(output, profile: profile)
    }
    public static func readSettingsOutput() -> String? {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/pmset")
        process.arguments = ["-g", "custom"]
        let pipe = Pipe(); process.standardOutput = pipe; process.standardError = FileHandle.nullDevice
        do {
            try process.run()
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            process.waitUntilExit()
            guard process.terminationStatus == 0 else { return nil }
            return String(decoding: data, as: UTF8.self)
        } catch { return nil }
    }
    public static func parseBatteryMode(_ output: String) -> Int? {
        parseMode(output, profile: .battery)
    }
    public static func parseMode(_ output: String, profile: LowPowerProfile) -> Int? {
        parseSettings(output, profile: profile)?.mode
    }
    private static func parseSettings(_ output: String, profile: LowPowerProfile) -> (key: String, mode: Int, hasHighPower: Bool)? {
        var inProfile = false
        var legacy: Int?
        var highPower: Int?
        for line in output.split(separator: "\n") {
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            if trimmed.hasSuffix("Power:") {
                inProfile = trimmed == (profile == .battery ? "Battery Power:" : "AC Power:")
                continue
            }
            let fields = trimmed.split(whereSeparator: \.isWhitespace)
            guard inProfile, fields.count == 2, let mode = Int(fields[1]) else { continue }
            if fields[0] == "powermode", (0...2).contains(mode) { return ("powermode", mode, true) }
            if fields[0] == "lowpowermode", (0...1).contains(mode) { legacy = mode }
            if fields[0] == "highpowermode", (0...1).contains(mode) { highPower = mode }
        }
        guard let legacy, !(legacy == 1 && highPower == 1) else { return nil }
        return ("lowpowermode", highPower == 1 ? 2 : legacy, highPower != nil)
    }
    public func setBatteryMode(_ mode: Int) -> Bool { setMode(mode, profile: .battery) }
    public func setAdapterMode(_ mode: Int) -> Bool { setMode(mode, profile: .adapter) }
    private func setMode(_ mode: Int, profile: LowPowerProfile) -> Bool {
        guard let settings = settings(for: profile), (0...2).contains(mode),
              settings.hasHighPower || mode <= 1 else { return false }
        let arguments: [String]
        let powerFlag = profile == .battery ? "-b" : "-c"
        if settings.key == "powermode" {
            arguments = [powerFlag, "powermode", String(mode)]
        } else if settings.hasHighPower {
            // Older systems expose the two mutually exclusive switches separately.
            arguments = [powerFlag, "lowpowermode", mode == 1 ? "1" : "0",
                         "highpowermode", mode == 2 ? "1" : "0"]
        } else {
            arguments = [powerFlag, "lowpowermode", String(mode)]
        }
        guard runner.run("/usr/bin/pmset", arguments) else { return false }
        return self.settings(for: profile)?.mode == mode
    }
}
public struct NullBatteryLowPowerControl: BatteryLowPowerControlling {
    public init() {}
    public func batteryMode() -> Int? { nil }
    public func setBatteryMode(_ mode: Int) -> Bool { false }
}

/// Serializes XPC requests and retries failed restores. The daemon restores even after an app crash.
@MainActor @Observable
public final class ClosedLidLowPowerController {
    public enum Status: Equatable {
        case off, needsHelper, waitingForClosedDisplay, waitingForLid, waitingForBattery, switching, active, failed
    }
    public private(set) var batteryHolding = false
    public private(set) var adapterHolding = false
    public var holding: Bool { batteryHolding || adapterHolding }
    public var hasPendingRequests: Bool { requestedBattery || requestedAdapter }
    public private(set) var busy = false
    public private(set) var failed = false
    public private(set) var status: Status = .off
    @ObservationIgnored private let helper: PrivilegedHelperCalling
    @ObservationIgnored private var lastAttempt: Date?
    @ObservationIgnored private var arming = ThermalArming()
    @ObservationIgnored private var batteryLatched = false
    @ObservationIgnored private var requestedBattery = false
    @ObservationIgnored private var requestedAdapter = false
    @ObservationIgnored private var activeTask: Task<Void, Never>?
    @ObservationIgnored private var stopping = false
    @ObservationIgnored private var pausedUntilDisarmed = false
    public init(helper: PrivilegedHelperCalling) { self.helper = helper }
    public func tick(enabled: Bool, lidClosed: Bool?, closedDisplayActive: Bool?,
                     onBattery: Bool?, helperAvailable: Bool, allowOnAC: Bool = false, now: Date = Date()) {
        guard !stopping else { return }
        let armed = arming.update(lidClosed: lidClosed, sleepOverrideActive: closedDisplayActive)
        if let onBattery { batteryLatched = onBattery }
        let base = enabled && armed && helperAvailable
        if !base { pausedUntilDisarmed = false }
        let desiredBattery = base && !pausedUntilDisarmed && (batteryLatched || allowOnAC)
        let desiredAdapter = base && !pausedUntilDisarmed && allowOnAC
        let waiting: Status = !enabled || pausedUntilDisarmed ? .off : !helperAvailable ? .needsHelper
            : closedDisplayActive != true && !armed ? .waitingForClosedDisplay
            : !armed ? .waitingForLid : !batteryLatched && !allowOnAC ? .waitingForBattery : .active
        status = busy ? .switching : failed ? .failed : waiting
        guard !busy else { return }
        guard desiredBattery != requestedBattery || desiredAdapter != requestedAdapter
                || (failed && (requestedBattery || requestedAdapter)) else {
            if !desiredBattery && !desiredAdapter { failed = false; lastAttempt = nil; status = waiting }
            return
        }
        let needsRelease = (!desiredBattery && requestedBattery) || (!desiredAdapter && requestedAdapter)
        if failed, !needsRelease, (desiredBattery || desiredAdapter),
           let lastAttempt, now.timeIntervalSince(lastAttempt) < 15 { return }
        busy = true; lastAttempt = now; status = .switching
        activeTask = Task { [helper] in
            defer { activeTask = nil }
            var ok = true
            // Restore disabled profiles before engaging new ones. Remember failed
            // attempts too: a partially applied write still needs a release.
            if !desiredAdapter && requestedAdapter {
                let released = await Task.detached { helper.setAdapterLowPowerHold(false) }.value
                if released { requestedAdapter = false; adapterHolding = false }
                ok = released && ok
            }
            if !desiredBattery && requestedBattery {
                let released = await Task.detached { helper.setLowPowerHold(false) }.value
                if released { requestedBattery = false; batteryHolding = false }
                ok = released && ok
            }
            if desiredBattery && (!batteryHolding || failed) {
                requestedBattery = true
                let engaged = await Task.detached { helper.setLowPowerHold(true) }.value
                batteryHolding = engaged; ok = engaged && ok
            }
            if desiredAdapter && (!adapterHolding || failed) {
                requestedAdapter = true
                let engaged = await Task.detached { helper.setAdapterLowPowerHold(true) }.value
                adapterHolding = engaged; ok = engaged && ok
            }
            failed = !ok; busy = false; status = ok ? waiting : .failed
        }
    }
    public func stopAndWait() async {
        stopping = true; pausedUntilDisarmed = true
        defer { stopping = false }
        await activeTask?.value
        var ok = true
        if requestedAdapter {
            let released = await Task.detached { [helper] in helper.setAdapterLowPowerHold(false) }.value
            if released { requestedAdapter = false; adapterHolding = false }
            ok = released && ok
        }
        if requestedBattery {
            let released = await Task.detached { [helper] in helper.setLowPowerHold(false) }.value
            if released { requestedBattery = false; batteryHolding = false }
            ok = released && ok
        }
        failed = !ok; status = ok ? .off : .failed
    }
}
