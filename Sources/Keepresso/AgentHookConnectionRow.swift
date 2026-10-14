import SwiftUI
import KeepressoCore

/// One presentation of hook state for both onboarding and Preferences.
struct AgentHookConnectionRow: View {
    @Bindable var model: AppModel
    let tool: AgentTool
    var compact = false
    @Environment(\.colorScheme) private var colorScheme
    private var state: AgentHooks.HookInstallState { model.hookState(of: tool) }
    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 10) {
                Image(assetName)
                    .renderingMode(.template).resizable().scaledToFit()
                    .foregroundStyle(tool == .claudeCode ? Color.keepressoBrew : Color.primary)
                    .frame(width: compact ? 20 : 24, height: compact ? 20 : 24)
                    .padding(7)
                    .background(.primary.opacity(0.05), in: RoundedRectangle(cornerRadius: 8))
                    .accessibilityHidden(true)
                VStack(alignment: .leading, spacing: 2) {
                    Text(verbatim: tool.displayName).font(compact ? .caption.weight(.medium) : .callout.weight(.medium))
                    if !compact {
                        Text(tool == .claudeCode || tool == .grok ? "CLI sessions" : "App and CLI sessions")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                }
                Spacer(minLength: 8)
                control
            }
            if case .installed = state {
                if tool == .codex {
                    Text("Approve new hooks in Codex before they can run.")
                        .font(.caption).foregroundStyle(.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                } else if tool == .grok && !compact {
                    Text("Reload hooks in a running Grok session (/hooks, then r) or start a new one.")
                        .font(.caption).foregroundStyle(.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
            if let error = model.hookError(for: tool) {
                Label(error, systemImage: "exclamationmark.triangle")
                    .font(.caption).foregroundStyle(.orange)
            }
        }
        .padding(.vertical, compact ? 2 : 4)
        .accessibilityElement(children: .contain)
    }
    @ViewBuilder private var control: some View {
        switch state {
        case .installed:
            Label("Installed", systemImage: "checkmark.circle.fill")
                .font(.caption).foregroundStyle(colorScheme == .dark ? Color.green : Color(red: 0.08, green: 0.42, blue: 0.18))
            Menu {
                Button("Remove") { model.removeAgentToolHooks(tool) }
            } label: { Image(systemName: "ellipsis") }
                .menuIndicator(.hidden).fixedSize()
                .accessibilityLabel(L("Manage %@ hooks", tool.displayName))
        case .notInstalled:
            Button("Connect") { model.connectAgentTool(tool) }.controlSize(.small)
        case .needsRepair:
            Button { model.connectAgentTool(tool) } label: {
                Label("Repair", systemImage: "wrench.and.screwdriver")
            }.controlSize(.small)
        case .unreadable:
            Label("Couldn't be read", systemImage: "exclamationmark.triangle")
                .font(.caption).foregroundStyle(.orange)
        }
    }
    private var assetName: String {
        switch tool {
        case .claudeCode: return "brand_claude_code"
        case .cursor: return "brand_cursor"
        case .codex: return "brand_codex"
        case .antigravity: return "brand_antigravity"
        case .grok: return "brand_grok"
        }
    }
}

extension AppModel {
    func removeAgentToolHooks(_ tool: AgentTool) {
        switch tool {
        case .claudeCode: removeClaudeHooks()
        case .cursor: removeCursorHooks()
        case .codex: removeCodexHooks()
        case .antigravity: removeAntigravityHooks()
        case .grok: removeGrokHooks()
        }
    }
    func hookError(for tool: AgentTool) -> String? {
        switch tool {
        case .claudeCode: return claudeHooksError
        case .cursor: return cursorHooksError
        case .codex: return codexHooksError
        case .antigravity: return antigravityHooksError
        case .grok: return grokHooksError
        }
    }
}
