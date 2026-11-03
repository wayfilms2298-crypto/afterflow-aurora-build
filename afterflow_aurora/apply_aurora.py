#!/usr/bin/env python3
"""Transactionally upgrade pinned Afterflow 2.2 source with Aurora UI + diagnostics.
Usage: python apply_aurora.py path/to/afterflow-source
MIT upstream; non-destructive until all code anchors validate.
"""
from __future__ import annotations
import argparse, json, tempfile, shutil
from pathlib import Path
from slate_core import patch as apply_slate, replace_once

MODE_NAMES = ('cube','ship','ball','ufo','wave','robot','spider','swing')

def r(source, old, new, label):
    return replace_once(source, old, new, label)

def update(root: Path):
    src_file = root / 'src/main.cpp'
    mod_file = root / 'mod.json'
    if not src_file.exists() or not mod_file.exists():
        raise RuntimeError('Provide the cloned source repository root, not your compiled .geode file.')
    original_src, original_mod = src_file.read_text(encoding='utf-8'), mod_file.read_text(encoding='utf-8')
    if 'AURORA_EXTENSION_V1' in original_src or 'SLATE_UI_PATCH' in original_src:
        raise RuntimeError('Already patched, please start from the clean pinned commit.')
    with tempfile.TemporaryDirectory(prefix='aurora-patch-') as tmp:
        staged = Path(tmp)
        (staged/'src').mkdir()
        (staged/'src/main.cpp').write_text(original_src, encoding='utf-8')
        (staged/'mod.json').write_text(original_mod, encoding='utf-8')
        apply_slate(staged)
        src = (staged/'src/main.cpp').read_text(encoding='utf-8')
        info = json.loads((staged/'mod.json').read_text(encoding='utf-8'))
        settings = info['settings']
        settings.update({
            'aurora-title': {'type':'title','name':'Aurora: analytics and adaptation'},
            'aurora-adaptive': {'type':'bool','name':'adaptive input window','description':'reduce correction window while rapid inputs are detected','default':False},
            'aurora-conservative': {'type':'bool','name':'conservative protection','description':'limit correction window to 80% of the configured range','default':False},
            'aurora-hud': {'type':'bool','name':'mini telemetry HUD','description':'show number of queued corrections in-game','default':False},
            'aurora-level-profiles': {'type':'bool','name':'auto-load level profile','description':'load a saved profile when entering its level','default':True},
            'aurora-visualizer': {'type':'bool','name':'correction timeline','description':'show correction timing graph in Insights','default':True},
            'aurora-appearance-title': {'type':'title','name':'Aurora motion and geometry'},
            'aurora-rounding': {'type':'float','name':'panel corner radius','default':22.0,'min':6.0,'max':32.0,'step':1.0},
            'aurora-opacity': {'type':'float','name':'panel opacity','default':0.96,'min':0.65,'max':1.0,'step':0.05},
            'aurora-reduce-motion': {'type':'bool','name':'reduce motion','description':'disable decorative animation, preserve function','default':False},
            'keybind-aurora-palette': {'type':'keybind','name':'open commands','category':'universal','default':['F7']},
            'keybind-aurora-safety': {'type':'keybind','name':'emergency bypass','category':'gameplay','default':['F8']},
            'aurora-mode-title': {'type':'title','name':'per-mode tuning'},
        })
        for mode in MODE_NAMES:
            settings[f'aurora-{mode}-mult'] = {'type':'float','name':f'{mode}: timing multiplier',
                'description':'scales the selected stage window only for this gamemode',
                'default':1.0,'min':0.3,'max':1.5,'step':0.05}
            settings[f'aurora-{mode}-press'] = {'type':'bool','name':f'{mode}: correct presses','default':True}
            settings[f'aurora-{mode}-release'] = {'type':'bool','name':f'{mode}: correct releases','default':True}
        info['description'] = 'Afterflow Aurora: adaptive prediction controls, session diagnostics, command search, profiles and fluid UI.'
        # Distinguish this fork from official Afterflow and previous Aurora builds.
        # Geode caches compiled DLLs by mod identity/version, so a unique version
        # is essential when installing over a 2.2.0 custom build.
        info['name'] = 'Afterflow Aurora'
        info['version'] = '3.0.0'
        info['description'] = 'Aurora V3: redesigned sidebar UI, native input controls, profiles, and telemetry. Based on Afterflow by sevend.'


        # New state helpers live inside the original anonymous namespace.
        src = r(src, '    constexpr int MOD_HOOK_PRIORITY = -1000000;', '''    // AURORA_EXTENSION_V1: telemetry measures input events and QUEUED corrections,
    // not guaranteed saved lives or accuracy. Bounded in-memory ring for privacy/performance.
    struct AuroraSample { int ticks = 0; bool press = false; int mode = 0; };
    struct AuroraMetrics {
        uint64_t inputCount = 0, queuedCount = 0, pressCount = 0, releaseCount = 0;
        uint64_t queuedTickSum = 0;
        int lastTicks = 0;
        std::deque<AuroraSample> history;
        void recordInput(bool press) { ++inputCount; press ? ++pressCount : ++releaseCount; }
        void recordQueue(int ticks, bool press, int mode) {
            if (ticks <= 0) return;
            ++queuedCount; queuedTickSum += static_cast<uint64_t>(ticks); lastTicks = ticks;
            history.push_back({ticks, press, mode});
            if (history.size() > 80) history.pop_front();
        }
        void clear() { *this = AuroraMetrics{}; }
    };
    AuroraMetrics g_aurora;
    int g_auroraCurrentMode = 0;

    constexpr int MOD_HOOK_PRIORITY = -1000000;''', 'telemetry storage')

        # Safety keybind: saved state persists until explicitly reset, ensuring deliberate opt-in.
        src = r(src, '    void setupKeybinds() {', '''    void resetPending();
    void openAuroraCommands();
    void setupKeybinds() {''', 'forward declarations')
        src = r(src, '''                toggleAfterflowPanel();
            }
            return true;
        });
    }

    constexpr char const* VERSION_URL''', '''                toggleAfterflowPanel();
            }
            return true;
        });
        listenForKeybindSettingPresses("keybind-aurora-palette", [](Keybind const&, bool down, bool repeat, double) {
            if (down && !repeat) openAuroraCommands();
            return true;
        });
        listenForKeybindSettingPresses("keybind-aurora-safety", [](Keybind const&, bool down, bool repeat, double) {
            if (down && !repeat) {
                bool next = !Mod::get()->getSavedValue<bool>("aurora-bypass", false);
                Mod::get()->setSavedValue<bool>("aurora-bypass", next);
                resetPending();
                geode::log::info("Aurora emergency bypass: {}", next ? "ON" : "OFF");
            }
            return true;
        });
    }

    constexpr char const* VERSION_URL''', 'native keybinds')

        # Helpers added after the original Slate input mode helper.
        src = r(src, '''    float uiMotion() {
        return static_cast<float>(Mod::get()->getSettingValue<double>("ui-motion"));
    }
''', '''    float uiMotion() {
        if (Mod::get()->getSettingValue<bool>("aurora-reduce-motion")) return 0.01f;
        return static_cast<float>(Mod::get()->getSettingValue<double>("ui-motion"));
    }

    constexpr char const* AURORA_MODES[8] = {
        "cube", "ship", "ball", "ufo", "wave", "robot", "spider", "swing"
    };
    int auroraModeIndex(PlayerObject* p) {
        if (!p) return 0;
        return p->m_isShip ? 1 : p->m_isBall ? 2 : p->m_isBird ? 3 :
            p->m_isDart ? 4 : p->m_isRobot ? 5 : p->m_isSpider ? 6 : p->m_isSwing ? 7 : 0;
    }
    double auroraModeMultiplier(int mode) {
        return Mod::get()->getSettingValue<double>(fmt::format("aurora-{}-mult", AURORA_MODES[std::clamp(mode, 0, 7)]));
    }
    bool auroraModeActionAllowed(int mode, bool down) {
        return Mod::get()->getSettingValue<bool>(fmt::format("aurora-{}-{}",
            AURORA_MODES[std::clamp(mode, 0, 7)], down ? "press" : "release"));
    }
    std::string auroraProfileKey(int slot) { return fmt::format("aurora-slot-{}", slot); }

    // All settings are saved as a versioned, delimited value. Missing/invalid data leaves settings alone.
    void auroraSaveProfile(std::string const& key) {
        std::string value = "A1";
        auto add = [&](double number) { value += ";" + fmt::format("{:.4f}", number); };
        add(Mod::get()->getSettingValue<double>("input-strength"));
        add(Mod::get()->getSettingValue<bool>("input-enabled") ? 1 : 0);
        add(Mod::get()->getSettingValue<bool>("aurora-adaptive") ? 1 : 0);
        add(Mod::get()->getSettingValue<bool>("aurora-conservative") ? 1 : 0);
        for (int i = 0; i < 8; ++i) {
            add(Mod::get()->getSettingValue<bool>(fmt::format("input-{}", AURORA_MODES[i])) ? 1 : 0);
            add(auroraModeMultiplier(i));
            add(auroraModeActionAllowed(i, true) ? 1 : 0);
            add(auroraModeActionAllowed(i, false) ? 1 : 0);
        }
        Mod::get()->setSavedValue<std::string>(key, value);
        (void)Mod::get()->saveData();
    }
    void resetPending();
    bool auroraLoadProfile(std::string const& key) {
        std::string raw = Mod::get()->getSavedValue<std::string>(key, "");
        if (raw.rfind("A1;", 0) != 0) return false;
        std::vector<double> values;
        size_t start = 3;
        try {
            while (start <= raw.size()) {
                size_t end = raw.find(';', start);
                if (end == std::string::npos) end = raw.size();
                values.push_back(std::stod(raw.substr(start, end - start)));
                start = end + 1;
                if (end == raw.size()) break;
            }
        } catch (...) { return false; }
        if (values.size() != 36) return false;
        auto bit = [&](size_t i) { return values[i] >= 0.5; };
        Mod::get()->setSettingValue<double>("input-strength", std::clamp(values[0], 0.5, 1.5));
        Mod::get()->setSettingValue<bool>("input-enabled", bit(1));
        Mod::get()->setSettingValue<bool>("aurora-adaptive", bit(2));
        Mod::get()->setSettingValue<bool>("aurora-conservative", bit(3));
        for (int i = 0; i < 8; ++i) {
            int j = 4 + i * 4;
            Mod::get()->setSettingValue<bool>(fmt::format("input-{}", AURORA_MODES[i]), bit(j));
            Mod::get()->setSettingValue<double>(fmt::format("aurora-{}-mult", AURORA_MODES[i]), std::clamp(values[j+1], 0.3, 1.5));
            Mod::get()->setSettingValue<bool>(fmt::format("aurora-{}-press", AURORA_MODES[i]), bit(j+2));
            Mod::get()->setSettingValue<bool>(fmt::format("aurora-{}-release", AURORA_MODES[i]), bit(j+3));
        }
        resetPending();
        return true;
    }
    void auroraApplyPreset(int id) {
        // Conservative defaults by design; never imply a perfect-input guarantee.
        static double const windows[] = { 0.7, 1.0, 1.35 };
        Mod::get()->setSettingValue<double>("input-strength", windows[std::clamp(id, 0, 2)]);
        Mod::get()->setSettingValue<bool>("aurora-adaptive", id == 1);
        Mod::get()->setSettingValue<bool>("aurora-conservative", id == 0);
        resetPending();
    }

    std::string auroraCSV() {
        std::string output = "queued_delay_ticks,action,gamemode\\n";
        for (auto const& sample : g_aurora.history) {
            output += fmt::format("{},{},{}\\n", sample.ticks,
                sample.press ? "press" : "release", AURORA_MODES[std::clamp(sample.mode, 0, 7)]);
        }
        return output;
    }
''', 'mode multiplier, profiler, CSV, adaptive utils')

        # Store actual recent input/queuing events, do not claim survival prediction precision.
        src = r(src, '''        state.isFirstPlayer = isFirstPlayer;
        state.hasRealInput = isDown;
        state.intendedOrbObject = nullptr;''', '''        state.isFirstPlayer = isFirstPlayer;
        state.hasRealInput = isDown;
        state.intendedOrbObject = nullptr;
        g_aurora.recordInput(isDown);''', 'track input even when bypassed')
        src = r(src, '''    void queueInput(int tickCount, bool isDown) {
        state.queuedInputs.push_back({ tickCount, isDown });
    }''', '''    void queueInput(int tickCount, bool isDown) {
        g_aurora.recordQueue(tickCount, isDown, g_auroraCurrentMode);
        state.queuedInputs.push_back({ tickCount, isDown });
    }''', 'queue telemetry')
        src = r(src, '''        auto* player1 = baseGameLayer->m_player1;
        auto* player2 = isDual ? playLayer->m_player2 : nullptr;''', '''        auto* player1 = baseGameLayer->m_player1;
        auto* player2 = isDual ? playLayer->m_player2 : nullptr;
        g_auroraCurrentMode = auroraModeIndex(player1);''', 'input mode telemetry')
        src = r(src, '''        if (!state.isEnabled || !Mod::get()->getSettingValue<bool>("input-enabled") ||
            !Mod::get()->getSettingValue<bool>(isDown ? "input-presses" : "input-releases")) {''', '''        if (!state.isEnabled || Mod::get()->getSavedValue<bool>("aurora-bypass", false) ||
            !Mod::get()->getSettingValue<bool>("input-enabled") ||
            !Mod::get()->getSettingValue<bool>(isDown ? "input-presses" : "input-releases")) {''', 'safety bypass')
        src = r(src, '''        if (!inputModeAllowed(player1) || (player2 && !inputModeAllowed(player2))) {''', '''        if (!inputModeAllowed(player1) || (player2 && !inputModeAllowed(player2)) ||
            !auroraModeActionAllowed(auroraModeIndex(player1), isDown) ||
            (player2 && !auroraModeActionAllowed(auroraModeIndex(player2), isDown))) {''', 'per-mode press/release')
        src = r(src, '''        maxDelayTicks = std::clamp(static_cast<int>(std::lround(maxDelayTicks *
            Mod::get()->getSettingValue<double>("input-strength"))), 0, st(60));''', '''        double multiplier = Mod::get()->getSettingValue<double>("input-strength") *
            auroraModeMultiplier(g_auroraCurrentMode);
        if (Mod::get()->getSettingValue<bool>("aurora-adaptive")) {
            // Input density provides a deterministic and bounded adaptation, not ML.
            multiplier *= std::clamp(1.08 - 0.10 * state.rapidInputTicks, 0.55, 1.08);
        }
        if (Mod::get()->getSettingValue<bool>("aurora-conservative")) {
            multiplier = std::min(multiplier, 0.80);
        }
        maxDelayTicks = std::clamp(static_cast<int>(std::lround(maxDelayTicks * multiplier)), 0, st(60));''', 'adaptive and per-mode tuning')
        src = r(src, '''        readSettings();
        applyStage();
        state.ghostPlayer1 = makeGhost(this);''', '''        readSettings();
        if (gameLevel && Mod::get()->getSettingValue<bool>("aurora-level-profiles")) {
            auroraLoadProfile(fmt::format("aurora-level-{}", gameLevel->m_levelID));
        }
        applyStage();
        g_aurora.clear();
        state.ghostPlayer1 = makeGhost(this);''', 'per-level profiles and session reset')

        # Modern 6-tab layout: Activity / Stages / Controls / Insights / Commands / Style.
        src = r(src, '''    constexpr int TAB_COUNT = 4;''', '''    constexpr int TAB_COUNT = 6;''', 'navigation expansion')
        src = r(src, '''static char const* names[TAB_COUNT] = { "activity", "stages", "controls", "style" };''',
            '''static char const* names[TAB_COUNT] = { "activity", "stages", "controls", "insights", "commands", "style" };''', '6 labels')
        # The original Slate appearance tab moved from index 3 to index 5.
        src = src.replace('if (m_activeTab == 3', 'if (m_activeTab == 5')
        src = src.replace('bool const showSettings = m_activeTab == 3;', 'bool const showSettings = m_activeTab == 5;')

        src = r(src, '''            InputStrengthUp,''', '''            InputStrengthUp,
            AuroraInsight,
            AuroraCommand,''', 'action types')
        src = r(src, '''        CCNode* m_inputPane = nullptr;''', '''        CCNode* m_inputPane = nullptr;
        CCNode* m_insightsPane = nullptr;
        CCNode* m_commandsPane = nullptr;
        CCDrawNode* m_graph = nullptr;
        CCDrawNode* m_motionTrace = nullptr;
        CCLabelBMFont* m_metricsText = nullptr;
        CCLabelBMFont* m_metricsDetail = nullptr;
        TextInput* m_commandSearch = nullptr;
        CCLabelBMFont* m_hud = nullptr;
        CCNode* m_commandRows[8] = {};
        int m_commandOrder[8] = {};
        std::string m_commandQuery;
        float m_wavePhase = 0.f;
        void updateCommandResults();
        void runAuroraCommand(int id);
    public:
        void openCommands() { openPanel(); m_activeTab = 4; applyTab(); refresh(); }
    private:''', 'panel feature fields')
        src = r(src, '''        m_inputPane = nullptr;''', '''        m_inputPane = nullptr;
        m_insightsPane = nullptr;
        m_commandsPane = nullptr;
        m_graph = nullptr;
        m_motionTrace = nullptr;
        m_metricsText = nullptr;
        m_metricsDetail = nullptr;
        m_commandSearch = nullptr;
        for (auto& row : m_commandRows) row = nullptr;''', 'reset feature fields')

        # Add tiny overlay pulse and two full native panes before already-inserted control pane.
        start_marker = '        // Separate rounded, high-contrast controls page. Drawn within the existing UI.'
        display = r'''        // AURORA: motion trace sits under the header, driven by actual queued corrections.
        m_motionTrace = makeDrawNode();
        m_deck->addChild(m_motionTrace, 4);

        m_insightsPane = CCNode::create();
        m_deck->addChild(m_insightsPane, 3);
        if (auto* title = makeLabel("Session signals", true, 0.75f, getUITextColor())) {
            title->setAnchorPoint(CCPoint(0.f, 0.5f));
            title->setPosition(CCPoint(CONTENT_X + 20.f, 320.f));
            m_insightsPane->addChild(title);
        }
        m_metricsText = makeLabel("0 inputs / 0 queued corrections", false, 0.74f, softTextColor());
        m_metricsText->setAnchorPoint(CCPoint(0.f, 0.5f));
        m_metricsText->setPosition(CCPoint(CONTENT_X + 20.f, 284.f));
        m_insightsPane->addChild(m_metricsText);
        m_metricsDetail = makeLabel("No corrections queued", false, 0.62f, faintTextColor());
        m_metricsDetail->setAnchorPoint(CCPoint(0.f, 0.5f));
        m_metricsDetail->setPosition(CCPoint(CONTENT_X + 20.f, 257.f));
        m_insightsPane->addChild(m_metricsDetail);
        m_graph = makeDrawNode();
        m_insightsPane->addChild(m_graph);
        static char const* insightNames[8] = {
            "BALANCED", "PRECISION", "AGGRESSIVE", "COPY CSV",
            "SAVE SLOT", "LOAD SLOT", "VISUALIZER", "ADAPTIVE"
        };
        for (int i = 0; i < 8; ++i) {
            auto rect = CCRect(CONTENT_X + 20.f + (i % 4) * 154.f,
                91.f + (i / 4) * 49.f, 146.f, 37.f);
            auto* tile = makeDrawNode();
            drawCurvedRect(tile, rect, 12.f, color4(accentColor(), 26), color4(accentColor(), 87), 1.f);
            m_insightsPane->addChild(tile);
            if (auto* label = makeLabel(insightNames[i], false, 0.48f, getUITextColor())) {
                label->setPosition(CCPoint(rect.getMidX(), rect.getMidY()));
                m_insightsPane->addChild(label);
            }
        }

        m_commandsPane = CCNode::create();
        m_deck->addChild(m_commandsPane, 3);
        if (auto* title = makeLabel("Command center", true, 0.76f, getUITextColor())) {
            title->setAnchorPoint(CCPoint(0.f, 0.5f));
            title->setPosition(CCPoint(CONTENT_X + 20.f, 322.f));
            m_commandsPane->addChild(title);
        }
        m_commandSearch = TextInput::create(CONTENT_WIDTH - 100.f, "Search commands...");
        if (m_commandSearch) {
            m_commandSearch->setMaxCharCount(32);
            m_commandSearch->setPosition(CCPoint(DECK_WIDTH * 0.5f, 284.f));
            m_commandSearch->setCallback([this](std::string const& text) {
                m_commandQuery = text;
                updateCommandResults();
            });
            m_commandsPane->addChild(m_commandSearch, 3);
        }
        static char const* commandNames[8] = {
            "Toggle correction", "Emergency bypass (F8)", "Adaptive prediction",
            "Mini telemetry HUD", "Copy session CSV", "Reset session stats",
            "Save level profile", "Load level profile"
        };
        for (int i = 0; i < 8; ++i) {
            auto* item = CCNode::create();
            auto* back = makeDrawNode();
            drawCurvedRect(back, CCRect(-276.f, -16.f, 552.f, 32.f), 11.f,
                color4(255, 255, 255, 10), color4(255, 255, 255, 20), 1.f);
            item->addChild(back);
            if (auto* name = makeLabel(commandNames[i], false, 0.65f, softTextColor())) {
                name->setAnchorPoint(CCPoint(0.f, 0.5f));
                name->setPosition(CCPoint(-260.f, 0.f));
                item->addChild(name);
            }
            m_commandsPane->addChild(item, 3);
            m_commandRows[i] = item;
        }
        updateCommandResults();

'''
        src = r(src, start_marker, display + start_marker, 'render Aurora Insights & Commands')
        src = r(src, '''        if (m_inputPane) { m_inputPane->setVisible(m_activeTab == 2); }''', '''        if (m_inputPane) { m_inputPane->setVisible(m_activeTab == 2); }
        if (m_insightsPane) { m_insightsPane->setVisible(m_activeTab == 3); }
        if (m_commandsPane) { m_commandsPane->setVisible(m_activeTab == 4); }''', 'insights commands visibility')

        # Tick refresh drives visual graph, animated top status pulse, and textual stats.
        src = r(src, '''    void AfterflowOverlay::refresh() {
        if (!m_deck) {
            return;
        }
''', '''    void AfterflowOverlay::refresh() {
        if (!m_deck) {
            return;
        }
        if (m_metricsText) {
            m_metricsText->setString(fmt::format("{} inputs     /     {} queued corrections",
                g_aurora.inputCount, g_aurora.queuedCount).c_str());
        }
        if (m_metricsDetail) {
            double avg = g_aurora.queuedCount ?
                static_cast<double>(g_aurora.queuedTickSum) / g_aurora.queuedCount : 0.0;
            m_metricsDetail->setString(fmt::format("press {}  /  release {}     |     avg {:.2f} ticks",
                g_aurora.pressCount, g_aurora.releaseCount, avg).c_str());
        }
        if (m_graph) {
            m_graph->clear();
            if (Mod::get()->getSettingValue<bool>("aurora-visualizer")) {
                auto back = CCRect(CONTENT_X + 20.f, 199.f, CONTENT_WIDTH - 40.f, 42.f);
                drawCurvedRect(m_graph, back, 10.f, color4(255,255,255,5), color4(255,255,255,17), 1.f);
                int total = static_cast<int>(g_aurora.history.size());
                int count = std::min(total, 48);
                for (int i = 0; i < count; ++i) {
                    auto const& sample = g_aurora.history[static_cast<size_t>(total - count + i)];
                    float amount = std::min(sample.ticks / 32.f, 1.f);
                    float x = back.getMinX() + 7.f + i * 12.35f;
                    float h = std::max(3.f, amount * 30.f);
                    m_graph->drawSegment(CCPoint(x, 205.f), CCPoint(x, 205.f + h),
                        2.2f, color4(sample.press ? accentColor() : secondaryColor(), 210));
                }
            }
        }
''', 'visual graph and metrics')
        src = r(src, '''        tutorialFrame(dt);
    }
''', '''        // Slow, non-distracting flowing trace. Disable with Reduce motion.
        if (m_motionTrace && m_activeTab >= 0) {
            m_motionTrace->clear();
            if (!Mod::get()->getSettingValue<bool>("aurora-reduce-motion")) m_wavePhase += dt * 1.8f;
            for (int i = 0; i < 58; ++i) {
                float x = CONTENT_X + 36.f + i * 10.f;
                float prior = static_cast<float>(g_aurora.lastTicks);
                float pulse = std::sin(m_wavePhase + i * 0.21f) * (1.0f + std::min(prior, 20.f) * 0.09f);
                float y = TAB_UNDERLINE_Y + 0.4f + pulse;
                float pulse2 = std::sin(m_wavePhase + (i + 1) * 0.21f) * (1.0f + std::min(prior, 20.f) * 0.09f);
                m_motionTrace->drawSegment(CCPoint(x, y), CCPoint(x + 10.f, TAB_UNDERLINE_Y + 0.4f + pulse2),
                    0.55f, color4(accentColor(), 32));
            }
        }
        tutorialFrame(dt);
    }
''', 'fluid header signal animation')

        # Hit detection for Insights/commands before other tabs. All controls react on release.
        src = r(src, '''    AfterflowOverlay::HitTarget AfterflowOverlay::hitTest(CCPoint const& point, int* stageSlot) const {
''', '''    AfterflowOverlay::HitTarget AfterflowOverlay::hitTest(CCPoint const& point, int* stageSlot) const {
        if (m_activeTab == 3) {
            for (int i = 0; i < 8; ++i) {
                CCRect cell(CONTENT_X + 20.f + (i % 4) * 154.f,
                    91.f + (i / 4) * 49.f, 146.f, 37.f);
                if (cell.containsPoint(point)) {
                    if (stageSlot) *stageSlot = i;
                    return HitTarget::AuroraInsight;
                }
            }
        }
        if (m_activeTab == 4) {
            for (int i = 0; i < 8; ++i) {
                if (m_commandOrder[i] >= 0 &&
                    CCRect(CONTENT_X + 50.f, 233.f - 37.f * i, 552.f, 34.f).containsPoint(point)) {
                    if (stageSlot) *stageSlot = m_commandOrder[i];
                    return HitTarget::AuroraCommand;
                }
            }
        }
''', 'insights and search hit test')
        src = r(src, '''bool isSameTarget = released == target &&
                ((target != HitTarget::StageSlot && target != HitTarget::InputOption &&
                  target != HitTarget::InputMode && target != HitTarget::Tab) ||
                 stageSlot == m_pressedStageSlot);''', '''bool isSameTarget = released == target &&
                ((target != HitTarget::StageSlot && target != HitTarget::InputOption &&
                  target != HitTarget::InputMode && target != HitTarget::AuroraInsight &&
                  target != HitTarget::AuroraCommand && target != HitTarget::Tab) ||
                 stageSlot == m_pressedStageSlot);''', 'gesture identity')
        src = r(src, '''        if (target == HitTarget::InputOption && m_pressedStageSlot >= 0 && m_pressedStageSlot < 3) {''', '''        if (target == HitTarget::AuroraCommand && m_pressedStageSlot >= 0 && m_pressedStageSlot < 8) {
            runAuroraCommand(m_pressedStageSlot);
            return;
        }
        if (target == HitTarget::AuroraInsight && m_pressedStageSlot >= 0 && m_pressedStageSlot < 8) {
            int const id = m_pressedStageSlot;
            if (id <= 2) auroraApplyPreset(id);
            if (id == 3) geode::utils::clipboard::write(auroraCSV().c_str());
            if (id == 4) auroraSaveProfile(auroraProfileKey(1));
            if (id == 5) auroraLoadProfile(auroraProfileKey(1));
            if (id == 6) Mod::get()->setSettingValue<bool>("aurora-visualizer",
                !Mod::get()->getSettingValue<bool>("aurora-visualizer"));
            if (id == 7) Mod::get()->setSettingValue<bool>("aurora-adaptive",
                !Mod::get()->getSettingValue<bool>("aurora-adaptive"));
            resetPending();
            refresh();
            return;
        }
        if (target == HitTarget::InputOption && m_pressedStageSlot >= 0 && m_pressedStageSlot < 3) {''', 'insights actions')

        command_impl = r'''    void AfterflowOverlay::updateCommandResults() {
        static char const* names[8] = {
            "Toggle correction", "Emergency bypass (F8)", "Adaptive prediction",
            "Mini telemetry HUD", "Copy session CSV", "Reset session stats",
            "Save level profile", "Load level profile"
        };
        std::string query = m_commandQuery;
        std::transform(query.begin(), query.end(), query.begin(),
            [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
        int next = 0;
        for (int i = 0; i < 8; ++i) {
            std::string title = names[i];
            std::transform(title.begin(), title.end(), title.begin(),
                [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
            bool visible = query.empty() || title.find(query) != std::string::npos;
            if (m_commandRows[i]) {
                m_commandRows[i]->setVisible(visible);
                if (visible) {
                    m_commandRows[i]->setPosition(CCPoint(DECK_WIDTH * 0.5f, 250.f - 37.f * next));
                }
            }
            if (visible && next < 8) m_commandOrder[next++] = i;
        }
        while (next < 8) m_commandOrder[next++] = -1;
    }

    void AfterflowOverlay::runAuroraCommand(int id) {
        switch (id) {
            case 0: Mod::get()->setSettingValue<bool>("input-enabled",
                !Mod::get()->getSettingValue<bool>("input-enabled")); break;
            case 1: Mod::get()->setSavedValue<bool>("aurora-bypass",
                !Mod::get()->getSavedValue<bool>("aurora-bypass", false)); break;
            case 2: Mod::get()->setSettingValue<bool>("aurora-adaptive",
                !Mod::get()->getSettingValue<bool>("aurora-adaptive")); break;
            case 3: Mod::get()->setSettingValue<bool>("aurora-hud",
                !Mod::get()->getSettingValue<bool>("aurora-hud")); break;
            case 4: geode::utils::clipboard::write(auroraCSV().c_str()); break;
            case 5: g_aurora.clear(); break;
            case 6: {
                auto* play = GameManager::get()->m_playLayer;
                if (play && play->m_level) auroraSaveProfile(fmt::format("aurora-level-{}", play->m_level->m_levelID));
                break;
            }
            case 7: {
                auto* play = GameManager::get()->m_playLayer;
                if (play && play->m_level) auroraLoadProfile(fmt::format("aurora-level-{}", play->m_level->m_levelID));
                break;
            }
        }
        resetPending();
        refresh();
    }

'''
        src = r(src, '''    void AfterflowOverlay::copyLog() {''', command_impl + '''    void AfterflowOverlay::copyLog() {''', 'command palette actions')
        # native F7 opener defined near existing native F9 toggler.
        src = r(src, '''    void toggleAfterflowPanel() {''', '''    void openAuroraCommands() {
        if (auto* overlay = activeAfterflowOverlay()) overlay->openCommands();
    }

    void toggleAfterflowPanel() {''', 'quick palette F7 opener')
        # Native mini HUD is rendered outside modal deck; updates while playing even if menu is closed.
        src = r(src, '''        buildDeck();

        m_launcher = CCNode::create();''', '''        buildDeck();
        m_hud = makeLabel("Aurora  |  0 queued", false, 0.60f, getUITextColor());
        if (m_hud) {
            m_hud->setPosition(CCPoint(winSize.width * 0.5f, winSize.height - 32.f));
            m_hud->setVisible(false);
            addChild(m_hud, 3);
        }
        schedule(schedule_selector(AfterflowOverlay::tickRefresh), 0.25f);

        m_launcher = CCNode::create();''', 'native telemetry HUD')
        src = r(src, '''    void AfterflowOverlay::tickRefresh(float) {
        if (m_isOpen) {
            refresh();
        }
    }''', '''    void AfterflowOverlay::tickRefresh(float) {
        if (m_hud) {
            bool show = Mod::get()->getSettingValue<bool>("aurora-hud") &&
                !m_isOpen && GameManager::get()->m_playLayer;
            m_hud->setVisible(show);
            if (show) {
                m_hud->setString(fmt::format("AURORA  |  {} inputs  |  {} queued  |  last +{}t",
                    g_aurora.inputCount, g_aurora.queuedCount, g_aurora.lastTicks).c_str());
            }
        }
        if (m_isOpen) refresh();
    }''', 'HUD updates')
        src = r(src, '''        endTickEdit();
        m_isOpen = false;
        unschedule(schedule_selector(AfterflowOverlay::tickRefresh));''',
            '''        endTickEdit();
        m_isOpen = false;
        // Keep the lightweight HUD scheduler active while the panel is closed.''', 'continuous stats')
        src = r(src, '        schedule(schedule_selector(AfterflowOverlay::tickRefresh), 0.2f);',
            '        // HUD timer was started in init().', 'avoid duplicate HUD schedule')
        src = r(src, '''        m_inputPane = CCNode::create();''', '''        m_inputPane = CCNode::create();''', 'noop') if False else src

        # Smooth, restrained motion. Angular velocity and cards driven by native Cocos actions.
        src = r(src, '''m_deck->setScale(m_deckScale * 0.88f);''', '''m_deck->setScale(m_deckScale * 0.94f);''', 'refined open scale')
        src = r(src, '''m_deck->runAction(CCEaseOut::create(CCScaleTo::create(0.25f * uiMotion(), m_deckScale), 2.f));''',
            '''m_deck->runAction(CCEaseOut::create(CCScaleTo::create(0.36f * uiMotion(), m_deckScale), 3.2f));''', 'smooth 360ms menu entrance')
        src = r(src, '''    constexpr float DECK_RADIUS = 27.f;''', '''    constexpr float DECK_RADIUS = 27.f;''', 'deck curvature marker') if False else src
        src = r(src, '''drawCurvedRect(m_shell, CCRect(0.f, 0.f, DECK_WIDTH, DECK_HEIGHT), DECK_RADIUS, color4(shellTint, 252), color4(255, 255, 255, 26), 1.f);''',
            '''drawCurvedRect(m_shell, CCRect(0.f, 0.f, DECK_WIDTH, DECK_HEIGHT),
            static_cast<float>(Mod::get()->getSettingValue<double>("aurora-rounding")),
            color4(shellTint, static_cast<int>(255 * Mod::get()->getSettingValue<double>("aurora-opacity"))),
            color4(255, 255, 255, 30), 1.f);''', 'user adjustable panel curvature and opacity')

        # The built-in status badge reflects emergency bypass and the new master switch.
        src = r(src, '        ccColor3B live = state.isEnabled ? accentColor() : warningColor();',
            '''        bool auroraLive = state.isEnabled && Mod::get()->getSettingValue<bool>("input-enabled") &&
            !Mod::get()->getSavedValue<bool>("aurora-bypass", false);
        ccColor3B live = auroraLive ? accentColor() : warningColor();''', 'accurate enabled badge color')
        src = r(src, 'm_statusLabel->setString(state.isEnabled ? "buffer on" : "buffer off");',
            'm_statusLabel->setString(auroraLive ? "buffer on" : "buffer off");', 'accurate enabled badge text')

        # When setting tabs, initial fade on individual section's child layers.
        src = r(src, '''        if (m_commandsPane) { m_commandsPane->setVisible(m_activeTab == 4); }''', '''        if (m_commandsPane) { m_commandsPane->setVisible(m_activeTab == 4); }
        if (!Mod::get()->getSettingValue<bool>("aurora-reduce-motion")) {
            CCNodeRGBA* pages[] = { m_inputPane, m_insightsPane, m_commandsPane };
            int ids[] = { 2, 3, 4 };
            for (int i = 0; i < 3; ++i) {
                if (pages[i] && m_activeTab == ids[i]) {
                    pages[i]->stopAllActions();
                    pages[i]->setOpacity(155);
                    pages[i]->runAction(CCFadeTo::create(0.24f * uiMotion(), 255));
                }
            }
        }''', 'per-tab fade')
        # Fix node opacity: CCNode is not necessarily RGBA; instead use CCNodeRGBA type to support fade.
        src = src.replace('m_inputPane = CCNode::create();', 'm_inputPane = CCNodeRGBA::create();')
        src = r(src, 'CCNode* m_inputPane = nullptr;', 'CCNodeRGBA* m_inputPane = nullptr;', 'RGBA input page')
        src = r(src, 'CCNode* m_insightsPane = nullptr;', 'CCNodeRGBA* m_insightsPane = nullptr;', 'RGBA insights page')
        src = r(src, 'CCNode* m_commandsPane = nullptr;', 'CCNodeRGBA* m_commandsPane = nullptr;', 'RGBA commands page')
        src = src.replace('m_insightsPane = CCNode::create();', 'm_insightsPane = CCNodeRGBA::create();')
        src = src.replace('m_commandsPane = CCNode::create();', 'm_commandsPane = CCNodeRGBA::create();')

        # AURORA_VISUAL_POLISH_V2
        # Large type, quiet surfaces, compact status, readable stage geometry.
        # This is applied to the finished Aurora source, not the original binary.
        src = r(src, 'constexpr float FONT_SCALE_BOOST = 1.0f;',
            'constexpr float FONT_SCALE_BOOST = 1.14f;', 'visual: typography contrast')
        src = r(src, 'constexpr float DECK_RADIUS = 27.f;',
            'constexpr float DECK_RADIUS = 20.f;', 'visual: shell curvature')
        src = r(src, 'constexpr float CARD_RADIUS = 19.f;',
            'constexpr float CARD_RADIUS = 15.f;', 'visual: pane curvature')
        src = r(src, 'constexpr float CARD_BOTTOM = 76.f;',
            'constexpr float CARD_BOTTOM = 52.f;', 'visual: reclaim bottom whitespace')
        src = r(src, 'constexpr float STAGE_META_Y = 274.f;',
            'constexpr float STAGE_META_Y = 282.f;', 'visual: compact stage heading')
        src = r(src, 'constexpr float STAGE_TRACK_Y = 212.f;',
            'constexpr float STAGE_TRACK_Y = 218.f;', 'visual: preset selector position')
        src = r(src, 'constexpr float STAGE_BAR_X = 430.f;',
            'constexpr float STAGE_BAR_X = 388.f;', 'visual: wider bar region')
        src = r(src, 'constexpr float STAGE_HINT_Y = 94.f;',
            'constexpr float STAGE_HINT_Y = 76.f;', 'visual: footer position')

        src = r(src,
            'drawCurvedRect(m_shell, CCRect(-12.f, -22.f, DECK_WIDTH + 24.f, DECK_HEIGHT + 22.f), DECK_RADIUS + 6.f, color4(0, 0, 0, 72), none, 0.f);',
            'drawCurvedRect(m_shell, CCRect(-8.f, -12.f, DECK_WIDTH + 16.f, DECK_HEIGHT + 16.f), DECK_RADIUS + 4.f, color4(0, 0, 0, 32), none, 0.f);',
            'visual: subtle outer shadow')
        src = r(src,
            'drawCurvedRect(m_shell, CCRect(CONTENT_X, CARD_BOTTOM, CONTENT_WIDTH, CARD_HEIGHT), CARD_RADIUS, color4(surface, 255), color4(255, 255, 255, 18), 1.f);',
            'drawCurvedRect(m_shell, CCRect(CONTENT_X, CARD_BOTTOM, CONTENT_WIDTH, CARD_HEIGHT), CARD_RADIUS, color4(surface, 250), color4(255, 255, 255, 10), 0.7f);',
            'visual: flat content surface')

        src = r(src,
            'makeLabel(tabName(tabIndex), true, 0.66f, faintTextColor())',
            'makeLabel(tabName(tabIndex), true, 0.76f, faintTextColor())',
            'visual: readable navigation')
        src = r(src,
            'm_tabLabels[index]->setOpacity(isActive ? 255 : 185);',
            'm_tabLabels[index]->setOpacity(isActive ? 255 : 215);',
            'visual: legible inactive navigation')
        src = r(src,
            'color4(accentColor(), 26),\n            color4(accentColor(), 74),\n            1.f\n        );',
            'color4(255, 255, 255, 14),\n            color4(255, 255, 255, 0),\n            0.f\n        );',
            'visual: quiet tab indicator')
        src = r(src,
            'makeLabel("tight", true, 0.88f, color3(240, 241, 246))',
            'makeLabel("tight", true, 1.08f, color3(240, 241, 246))',
            'visual: stage headline')
        src = r(src,
            'makeLabel("01/08", true, 0.58f, accentColor())',
            'makeLabel("01/08", true, 0.72f, softTextColor())',
            'visual: stage index')
        src = r(src,
            'makeLabel("", false, 0.74f, softTextColor())',
            'makeLabel("", false, 0.84f, softTextColor())',
            'visual: stage explanation')
        src = r(src,
            'makeLabel(stageLabelAt(index), false, 0.58f, softTextColor())',
            'makeLabel(stageLabelAt(index), false, 0.74f, softTextColor())',
            'visual: stage chips')
        src = r(src,
            'makeLabel("all modes", false, 0.66f, softTextColor())',
            'makeLabel("all modes", false, 0.82f, softTextColor())',
            'visual: all-modes text')
        src = r(src,
            'makeLabel("wave", false, 0.66f, softTextColor())',
            'makeLabel("wave", false, 0.82f, softTextColor())',
            'visual: wave text')
        src = r(src,
            'makeLabel("tap a stage above to apply it", false, 0.60f, faintTextColor())',
            'makeLabel("Select a preset or create a custom window", false, 0.67f, faintTextColor())',
            'visual: useful footer')
        src = r(src,
            'makeLabel("0t", true, 0.62f, color3(240, 241, 246))',
            'makeLabel("0t", true, 0.84f, color3(240, 241, 246))',
            'visual: value typography')
        src = r(src,
            'm_tickValueLabels[row]->setScale(0.62f * getUIFontScale());',
            'm_tickValueLabels[row]->setScale(0.84f * getUIFontScale());',
            'visual: prevent refresh shrinking values')
        src = r(src,
            'makeLabel("+ custom", false, 0.62f, accentColor())',
            'makeLabel("+ custom", false, 0.76f, accentColor())',
            'visual: custom button')
        src = r(src,
            '''        m_stageTrack = makeDrawNode();
        m_deck->addChild(m_stageTrack, 1);''',
            '''        // Small section label clarifies the controls below the presets.
        if (auto* section = makeLabel("PREDICTION WINDOWS", false, 0.62f, faintTextColor())) {
            section->setAnchorPoint(CCPoint(0.f, 0.5f));
            section->setPosition(CCPoint(LOG_X + 22.f, 195.f));
            m_deck->addChild(section, 3);
            m_stageTimingLabels[3] = section;
        }
        m_stageTrack = makeDrawNode();
        m_deck->addChild(m_stageTrack, 1);''',
            'visual: timing section label')
        src = r(src,
            'color4(selectedTint, 48),\n                color4(selectedTint, 150),',
            'color4(selectedTint, 38),\n                color4(selectedTint, 62),',
            'visual: subtle preset selected state')
        src = r(src,
            'color4(255, 255, 255, 7),\n                color4(255, 255, 255, 14),',
            'color4(255, 255, 255, 8),\n                color4(255, 255, 255, 12),',
            'visual: subtle preset rail')
        src = r(src,
            '''                    6.f,
                    color4(255, 255, 255, 8),
                    color4(255, 255, 255, 24),
                    1.f''',
            '''                    8.f,
                    color4(255, 255, 255, 9),
                    color4(255, 255, 255, 12),
                    0.75f''',
            'visual: unobtrusive value tiles')

        # Simplify stage bars while preserving custom-stage drag behavior.
        old_bar_start = '            auto drawBar = [&](int barIndex, float y, ccColor3B tint) {'
        old_bar_end = '            drawBar(0, STAGE_TIMING_ALL_Y, live);'
        if src.count(old_bar_start) != 1 or src.count(old_bar_end) != 1:
            raise RuntimeError('Cannot locate stage bar renderer for visual polish.')
        a = src.index(old_bar_start)
        b = src.index(old_bar_end, a)
        new_bar = '''            auto drawBar = [&](int barIndex, float y, ccColor3B tint) {
                float const ticks = m_barShown[barIndex];
                constexpr float h = 10.f;
                drawCurvedRect(m_stageTrack,
                    CCRect(STAGE_BAR_X, y - h * .5f, STAGE_BAR_WIDTH, h), 5.f,
                    color4(255, 255, 255, 18), color4(0, 0, 0, 0), 0.f);
                float ratio = std::clamp(ticks / static_cast<float>(barMax), 0.f, 1.f);
                if (isCustomSelected) {
                    ratio = std::clamp(
                        (ticks - static_cast<float>(CUSTOM_TICKS_MIN)) /
                        static_cast<float>(CUSTOM_TICKS_MAX - CUSTOM_TICKS_MIN), 0.f, 1.f);
                }
                if (ticks > 0.5f) {
                    float const w = std::max(6.f, STAGE_BAR_WIDTH * ratio);
                    drawCurvedRect(m_stageTrack,
                        CCRect(STAGE_BAR_X, y - h * .5f, w, h), 5.f,
                        color4(tint, 185), color4(0, 0, 0, 0), 0.f);
                }
                if (isCustomSelected) {
                    float const knobX = STAGE_BAR_X + STAGE_BAR_WIDTH * ratio;
                    m_stageTrack->drawCircle(CCPoint(knobX, y), 7.f,
                        color4(244, 244, 250, 255), 0.f, color4(0, 0, 0, 0), 20);
                    m_stageTrack->drawCircle(CCPoint(knobX, y), 3.f,
                        color4(tint, 255), 0.f, color4(0, 0, 0, 0), 16);
                }
            };
'''
        src = src[:a] + new_bar + src[b:]
        # End visual polish; engine input behavior is otherwise unchanged.

        # This fork must never silently reinstall the upstream release over Aurora.
        src = r(src, '    void checkForUpdates(bool isLoud) {',
            '''    void checkForUpdates(bool isLoud) {
        (void)isLoud;
        return; // Aurora V3: disable upstream auto-update and rollback.''',
            'prevent upstream overwriting custom Aurora builds')

        # V3: replace the previous visual hierarchy with a genuinely new sidebar UI.
        from v3_shell import patch_string
        src = patch_string(src)
        from v4_shell import patch_string as patch_v4
        src = patch_v4(src)
        info['name'] = 'Afterflow Aurora'
        info['version'] = '4.0.0'
        info['description'] = 'Afterflow Aurora V4: retained native workspace, redesigned navigation, input controls, profiles, and local diagnostics. Based on Afterflow by sevend.'

        # Settings page reset and save window options via Geode. Extra data exists even if HUD isn't a native render.
        modified_mod = json.dumps(info, ensure_ascii=False, indent=2) + '\n'
        # Only after every anchor was satisfied, commit both files.
        (root/'src/main.cpp.before-aurora').write_text(original_src, encoding='utf-8')
        (root/'mod.json.before-aurora').write_text(original_mod, encoding='utf-8')
        src_file.write_text(src, encoding='utf-8')
        mod_file.write_text(modified_mod, encoding='utf-8')
        print('Aurora source patch applied. Build from this project with Geode. Original files backed up.')

if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('source',type=Path)
    args=p.parse_args()
    update(args.source.resolve())
