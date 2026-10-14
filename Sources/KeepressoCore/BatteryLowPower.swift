import Foundation
import Observation

public protocol BatteryLowPowerControlling: Sendable {
    func batteryMode() -> Int?
    func setBatteryMode(_ mode: Int) -> Bool
}
public struct PMSetBatteryLowPowerControl: BatteryLowPowerControlling {
    public init() {}
    public func batteryMode() -> Int? { batterySettings()?.mode }
    private func batterySettings() -> (key: String, mode: Int, hasHighPower: Bool)? {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/pmset")
        process.arguments = ["-g", "custom"]
        let pipe = Pipe(); process.standardOutput = pipe; process.standardError = FileHandle.nullDevice
        do {
            try process.run()
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            process.waitUntilExit()
            guard process.terminationStatus == 0 else { return nil }
            return Self.parseBatterySettings(String(decoding: data, as: UTF8.self))
        } catch { return nil }
    }
    public static func parseBatteryMode(_ output: String) -> Int? {
        parseBatterySettings(output)?.mode
    }
    private static func parseBatterySettings(_ output: String) -> (key: String, mode: Int, hasHighPower: Bool)? {
        var inBattery = false
        var legacy: Int?
        var highPower: Int?
        for line in output.split(separator: "\n") {
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            if trimmed.hasSuffix("Power:") { inBattery = trimmed == "Battery Power:"; continue }
            let fields = trimmed.split(whereSeparator: \.isWhitespace)
            guard inBattery, fields.count == 2, let mode = Int(fields[1]) else { continue }
            if fields[0] == "powermode", (0...2).contains(mode) { return ("powermode", mode, true) }
            if fields[0] == "lowpowermode", (0...1).contains(mode) { legacy = mode }
            if fields[0] == "highpowermode", (0...1).contains(mode) { highPower = mode }
        }
        guard let legacy, !(legacy == 1 && highPower == 1) else { return nil }
        return ("lowpowermode", highPower == 1 ? 2 : legacy, highPower != nil)
    }
    public func setBatteryMode(_ mode: Int) -> Bool {
        guard let settings = batterySettings(), (0...2).contains(mode),
              settings.hasHighPower || mode <= 1 else { return false }
        let arguments: [String]
        if settings.key == "powermode" {
            arguments = ["-b", "powermode", String(mode)]
        } else if settings.hasHighPower {
            // Older systems expose the two mutually exclusive switches separately.
            arguments = ["-b", "lowpowermode", mode == 1 ? "1" : "0",
                         "highpowermode", mode == 2 ? "1" : "0"]
        } else {
            arguments = ["-b", "lowpowermode", String(mode)]
        }
        return ProcessCommandRunner().run("/usr/bin/pmset", arguments)
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
    public private(set) var holding = false
    public private(set) var busy = false
    public private(set) var failed = false
    @ObservationIgnored private let helper: PrivilegedHelperCalling
    @ObservationIgnored private var lastAttempt: Date?
    @ObservationIgnored private var arming = ThermalArming()
    @ObservationIgnored private var batteryLatched = false
    @ObservationIgnored private var activeTask: Task<Void, Never>?
    @ObservationIgnored private var stopping = false
    @ObservationIgnored private var pausedUntilDisarmed = false
    public init(helper: PrivilegedHelperCalling) { self.helper = helper }
    public func tick(enabled: Bool, lidClosed: Bool?, closedDisplayActive: Bool?,
                     onBattery: Bool?, helperAvailable: Bool, now: Date = Date()) {
        guard !stopping else { return }
        let armed = arming.update(lidClosed: lidClosed, sleepOverrideActive: closedDisplayActive)
        if let onBattery { batteryLatched = onBattery }
        let base = enabled && armed && batteryLatched && helperAvailable
        if !base { pausedUntilDisarmed = false }
        let desired = base && !pausedUntilDisarmed
        guard !busy else { return }
        guard desired != holding else {
            if !desired { failed = false; lastAttempt = nil }
            return
        }
        if failed, let lastAttempt, now.timeIntervalSince(lastAttempt) < 15 { return }
        busy = true; lastAttempt = now
        activeTask = Task { [helper] in
            defer { activeTask = nil }
            let ok = await Task.detached { helper.setLowPowerHold(desired) }.value
            if ok { holding = desired }
            failed = !ok; busy = false
        }
    }
    public func stopAndWait() async {
        stopping = true; pausedUntilDisarmed = true
        defer { stopping = false }
        await activeTask?.value
        guard holding else { return }
        let ok = await Task.detached { [helper] in helper.setLowPowerHold(false) }.value
        if ok { holding = false }
        failed = !ok
    }

}
