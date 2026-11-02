#!/usr/bin/env python3
"""Apply an Apple-inspired input/UI panel patch to pinned Afterflow v2.2.0 source.
Does not modify compiled .geode. Transactional: write files only after all checks pass.
"""
import argparse
import json
from pathlib import Path

TARGET_COMMIT = '1ea283fde439f2cc418cce26eed6a097808c6336'


def replace_once(s, old, new, label):
    n = s.count(old)
    if n != 1:
        raise RuntimeError(f'Patch stopped at {label}: expected one exact code anchor, found {n}. '\
                           'Use the pinned source revision stated in README.')
    return s.replace(old, new, 1)


def patch(root):
    src = root / 'src' / 'main.cpp'
    mod = root / 'mod.json'
    if not src.exists() or not mod.exists():
        raise RuntimeError('Please supply the root of the downloaded Afterflow SOURCE project.')
    source = src.read_text(encoding='utf-8')
    info = json.loads(mod.read_text(encoding='utf-8'))
    if 'SLATE_UI_PATCH' in source:
        raise RuntimeError('This source already has the Slate patch.')
    if info.get('id') != 'afterflow.prsevend' or info.get('version') != '2.2.0':
        raise RuntimeError('Expected Afterflow 2.2.0 source; use the pinned commit in README.')

    # Geode native settings are live engine controls, not decorative defaults.
    fields = info['settings']
    fields.update({
        'input-title': {'type': 'title', 'name': 'input control', 'description': 'precision input controls'},
        'input-enabled': {'type':'bool','name':'enable correction','description':'master switch for input correction','default':True},
        'input-presses': {'type':'bool','name':'correct presses','description':'allow the predictor to adjust button presses','default':True},
        'input-releases': {'type':'bool','name':'correct releases','description':'allow the predictor to adjust button releases','default':True},
        'input-strength': {'type':'float','name':'correction window multiplier','description':'scale the selected stage timing window (1.0 = original behavior)','default':1.0,'min':0.5,'max':1.5,'step':0.05},
        'modes-title': {'type':'title','name':'gamemodes','description':'which gamemodes the predictor may adjust'},
        'input-cube': {'type':'bool','name':'cube','default':True},
        'input-ship': {'type':'bool','name':'ship','default':True},
        'input-ball': {'type':'bool','name':'ball','default':True},
        'input-ufo': {'type':'bool','name':'ufo','default':True},
        'input-wave': {'type':'bool','name':'wave','default':True},
        'input-robot': {'type':'bool','name':'robot','default':True},
        'input-spider': {'type':'bool','name':'spider','default':True},
        'input-swing': {'type':'bool','name':'swing','default':True},
        'ui-dim': {'type':'float','name':'background dimming','description':'overlay backdrop darkness','default':0.58,'min':0.1,'max':0.85,'step':0.05},
        'ui-motion': {'type':'float','name':'animation duration','description':'panel motion: 0.25 faster, 1.5 slower','default':1.0,'min':0.25,'max':1.5,'step':0.05},
    })
    for name,val in {
        'ui-primary-color':'#0A84FF', 'ui-secondary-color':'#FFFFFF',
        'ui-surface-color':'#1C1C1E', 'ui-text-color':'#F5F5F7',
        'ui-glow':False, 'ui-panel-scale':0.85, 'ui-font-scale':1.20
    }.items():
        if name in fields: fields[name]['default'] = val

    # Engine controls (raw path reverts to unmodified input and flushes the queue).
    source = replace_once(source,
        '    constexpr int TAB_COUNT = 3;',
        '''    // SLATE_UI_PATCH: clean controls tab + real engine options.
    constexpr int TAB_COUNT = 4;
    constexpr char const* INPUT_OPTION_KEYS[3] = {"input-enabled", "input-presses", "input-releases"};
    constexpr char const* INPUT_OPTION_NAMES[3] = {"Correction", "Press timing", "Release timing"};
    constexpr char const* INPUT_MODE_KEYS[8] = {
        "input-cube", "input-ship", "input-ball", "input-ufo",
        "input-wave", "input-robot", "input-spider", "input-swing"
    };
    constexpr char const* INPUT_MODE_NAMES[8] = {
        "Cube", "Ship", "Ball", "UFO", "Wave", "Robot", "Spider", "Swing"
    };''', 'tab count and settings')
    source = replace_once(source,
        'static char const* names[TAB_COUNT] = { "log", "stage", "settings" };',
        'static char const* names[TAB_COUNT] = { "activity", "stages", "controls", "style" };',
        'modern tab labels')

    # Changes in above tab naming: existing settings pane should move to index 3.
    # Only existing explicit 2-index tests in overlay methods are changed, leaving gameplay math intact.
    for prefix in ['if (m_activeTab == 2', 'bool const showSettings = m_activeTab == 2;',
                   'if (m_activeTab == 2 &&', 'if (m_activeTab == 2)']:
        # Replacement is intentionally global for UI tab 2 references.
        source = source.replace(prefix, prefix.replace('== 2','== 3'))
    # Styling preset and true control pane geometry.
    source = replace_once(source,
        '{ "violet", 0x7C4DFF, 0xB79CFF, 0x16161A, 0xE8E9EE },',
        '{ "macos",  0x0A84FF, 0xFFFFFF, 0x1C1C1E, 0xF5F5F7 },', 'native macOS theme')

    source = replace_once(source, '    constexpr float DECK_RADIUS = 10.f;',
                          '    constexpr float DECK_RADIUS = 27.f;', 'deck rounding')
    source = replace_once(source, '    constexpr float CARD_RADIUS = 8.f;',
                          '    constexpr float CARD_RADIUS = 19.f;', 'card rounding')

    # Helpers placed after UI getter, where PlayerObject and Mod definitions are visible.
    source = replace_once(source,
        '    std::filesystem::path macTerminalCommandPath() {',
        '''    bool inputModeAllowed(PlayerObject* player) {
        if (!player) return true;
        char const* key = player->m_isShip ? "input-ship"
            : player->m_isBall ? "input-ball"
            : player->m_isBird ? "input-ufo"
            : player->m_isDart ? "input-wave"
            : player->m_isRobot ? "input-robot"
            : player->m_isSpider ? "input-spider"
            : player->m_isSwing ? "input-swing" : "input-cube";
        return Mod::get()->getSettingValue<bool>(key);
    }

    float uiMotion() {
        return static_cast<float>(Mod::get()->getSettingValue<double>("ui-motion"));
    }

    std::filesystem::path macTerminalCommandPath() {''', 'UI and gameplay helpers')

    source = replace_once(source,
        '        if (!state.isEnabled) {\n            state.hasAppliedInput = isDown;\n            return false;\n        }',
        '''        if (!state.isEnabled || !Mod::get()->getSettingValue<bool>("input-enabled") ||
            !Mod::get()->getSettingValue<bool>(isDown ? "input-presses" : "input-releases")) {
            resetPending();
            state.hasAppliedInput = isDown;
            return false;
        }''', 'master and press/release bypass')
    source = replace_once(source,
        '        bool isOrbUnderClick = player1->m_touchingRings && player1->m_touchingRings->count() > 0;',
        '''        if (!inputModeAllowed(player1) || (player2 && !inputModeAllowed(player2))) {
            resetPending();
            state.hasAppliedInput = isDown;
            return false;
        }

        bool isOrbUnderClick = player1->m_touchingRings && player1->m_touchingRings->count() > 0;''',
        'gamemode bypass')
    source = replace_once(source,
        '        int maxDelayTicks = st(hasWave ? state.ticksWaveMode : (hasShip ? std::clamp(state.shipMaxDelayTicks, 0, 16) : state.ticksAllModes));',
        '''        int maxDelayTicks = st(hasWave ? state.ticksWaveMode : (hasShip ? std::clamp(state.shipMaxDelayTicks, 0, 16) : state.ticksAllModes));
        maxDelayTicks = std::clamp(static_cast<int>(std::lround(maxDelayTicks *
            Mod::get()->getSettingValue<double>("input-strength"))), 0, st(60));''',
        'working timing multiplier')

    # New panel is a child of the existing pausing/touch-blocking overlay.
    source = replace_once(source,
        '            SettingsRow,',
        '''            SettingsRow,
            InputOption,
            InputMode,
            InputStrengthDown,
            InputStrengthUp,''', 'new hit targets')
    source = replace_once(source,
        '        CCDrawNode* m_settingsBar = nullptr;',
        '''        CCDrawNode* m_settingsBar = nullptr;
        CCNode* m_inputPane = nullptr;''', 'control pane field')
    source = replace_once(source,
        '        m_settingsBar = nullptr;',
        '''        m_settingsBar = nullptr;
        m_inputPane = nullptr;''', 'control pane pointer reset')

    # Precise hitboxes and responsive painted controls.
    source = replace_once(source,
        '    // small credits button, pinned to the top right of the settings card',
        '''    CCRect inputOptionRect(int row) {
        return CCRect(CONTENT_X + 20.f, 259.f - 54.f * row, 278.f, 45.f);
    }
    CCRect inputModeRect(int index) {
        return CCRect(CONTENT_X + 333.f + (index % 2) * 150.f,
            269.f - (index / 2) * 46.f, 132.f, 38.f);
    }
    CCRect strengthRect(bool increase) {
        return CCRect(CONTENT_X + (increase ? 272.f : 221.f), 96.f, 42.f, 33.f);
    }

    // small credits button, pinned to the top right of the settings card''', 'new panel hit geometry')

    pane = '''        // Separate rounded, high-contrast controls page. Drawn within the existing UI.
        m_inputPane = CCNode::create();
        m_deck->addChild(m_inputPane, 3);
        if (auto* heading = makeLabel("Input correction", true, 0.72f, logTextColor())) {
            heading->setAnchorPoint(CCPoint(0.f, 0.5f));
            heading->setPosition(CCPoint(CONTENT_X + 20.f, 323.f));
            m_inputPane->addChild(heading);
        }
        auto* controlDraw = makeDrawNode();
        m_inputPane->addChild(controlDraw);
        for (int i = 0; i < 3; ++i) {
            bool on = Mod::get()->getSettingValue<bool>(INPUT_OPTION_KEYS[i]);
            auto rect = inputOptionRect(i);
            drawCurvedRect(controlDraw, rect, 15.f,
                on ? color4(accentColor(), 27) : color4(255, 255, 255, 8),
                on ? color4(accentColor(), 100) : color4(255, 255, 255, 24), 1.f);
            if (auto* label = makeLabel(fmt::format("{}    {}", INPUT_OPTION_NAMES[i], on ? "ON" : "OFF"),
                false, 0.66f, on ? getUITextColor() : faintTextColor())) {
                label->setAnchorPoint(CCPoint(0.f, 0.5f));
                label->setPosition(CCPoint(rect.getMinX() + 16.f, rect.getMidY()));
                m_inputPane->addChild(label, 1);
            }
        }
        for (int i = 0; i < 8; ++i) {
            bool on = Mod::get()->getSettingValue<bool>(INPUT_MODE_KEYS[i]);
            auto rect = inputModeRect(i);
            drawCurvedRect(controlDraw, rect, 13.f,
                on ? color4(accentColor(), 26) : color4(255, 255, 255, 8),
                on ? color4(accentColor(), 85) : color4(255, 255, 255, 22), 1.f);
            if (auto* label = makeLabel(fmt::format("{}  {}", INPUT_MODE_NAMES[i], on ? "ON" : "OFF"),
                false, 0.55f, on ? softTextColor() : faintTextColor())) {
                label->setPosition(CCPoint(rect.getMidX(), rect.getMidY()));
                m_inputPane->addChild(label, 1);
            }
        }
        auto strength = Mod::get()->getSettingValue<double>("input-strength");
        if (auto* label = makeLabel(fmt::format("Window  {:.2f}x", strength), false, 0.65f, softTextColor())) {
            label->setAnchorPoint(CCPoint(0.f, 0.5f));
            label->setPosition(CCPoint(CONTENT_X + 20.f, 112.f));
            m_inputPane->addChild(label, 1);
        }
        for (int i = 0; i < 2; ++i) {
            bool inc = i == 1;
            auto rect = strengthRect(inc);
            drawCurvedRect(controlDraw, rect, 12.f, color4(accentColor(), 29),
                           color4(accentColor(), 91), 1.f);
            if (auto* label = makeLabel(inc ? "+" : "-", true, 0.75f, getUITextColor())) {
                label->setPosition(CCPoint(rect.getMidX(), rect.getMidY()));
                m_inputPane->addChild(label, 1);
            }
        }

'''
    source = replace_once(source,
        '        applyTab();\n        buildTutorialLayer();', pane + '        applyTab();\n        buildTutorialLayer();',
        'draw the input controls page')
    source = replace_once(source,
        '        bool const showSettings = m_activeTab == 3;',
        '''        bool const showSettings = m_activeTab == 3;
        if (m_inputPane) { m_inputPane->setVisible(m_activeTab == 2); }''', 'page visibility')

    source = replace_once(source,
        '        if (m_activeTab == 3 && creditsRect().containsPoint(point)) {\n            return HitTarget::Credits;\n        }\n        if (m_activeTab == 3) {',
        '''        if (m_activeTab == 2) {
            for (int i = 0; i < 3; ++i) {
                if (inputOptionRect(i).containsPoint(point)) {
                    if (stageSlot) *stageSlot = i;
                    return HitTarget::InputOption;
                }
            }
            for (int i = 0; i < 8; ++i) {
                if (inputModeRect(i).containsPoint(point)) {
                    if (stageSlot) *stageSlot = i;
                    return HitTarget::InputMode;
                }
            }
            if (strengthRect(false).containsPoint(point)) return HitTarget::InputStrengthDown;
            if (strengthRect(true).containsPoint(point)) return HitTarget::InputStrengthUp;
        }
        if (m_activeTab == 3 && creditsRect().containsPoint(point)) {
            return HitTarget::Credits;
        }
        if (m_activeTab == 3) {''',
        'input page hit testing')
    source = replace_once(source,
        'bool isSameTarget = released == target && (target != HitTarget::StageSlot || stageSlot == m_pressedStageSlot);',
        '''bool isSameTarget = released == target &&
                ((target != HitTarget::StageSlot && target != HitTarget::InputOption &&
                  target != HitTarget::InputMode && target != HitTarget::Tab) ||
                 stageSlot == m_pressedStageSlot);''', 'safe gesture target matching')
    source = replace_once(source,
        '        if (target == HitTarget::SettingsRow) {',
        '''        if (target == HitTarget::InputOption && m_pressedStageSlot >= 0 && m_pressedStageSlot < 3) {
            auto* key = INPUT_OPTION_KEYS[m_pressedStageSlot];
            Mod::get()->setSettingValue<bool>(key, !Mod::get()->getSettingValue<bool>(key));
            resetPending();
            rebuildDeck();
            return;
        }
        if (target == HitTarget::InputMode && m_pressedStageSlot >= 0 && m_pressedStageSlot < 8) {
            auto* key = INPUT_MODE_KEYS[m_pressedStageSlot];
            Mod::get()->setSettingValue<bool>(key, !Mod::get()->getSettingValue<bool>(key));
            resetPending();
            rebuildDeck();
            return;
        }
        if (target == HitTarget::InputStrengthDown || target == HitTarget::InputStrengthUp) {
            double value = Mod::get()->getSettingValue<double>("input-strength");
            value = std::clamp(value + (target == HitTarget::InputStrengthUp ? 0.05 : -0.05), 0.5, 1.5);
            Mod::get()->setSettingValue<double>("input-strength", std::round(value * 20.0) / 20.0);
            rebuildDeck();
            return;
        }

        if (target == HitTarget::SettingsRow) {''', 'interactive controls')

    source = replace_once(source,
        'm_scrim->runAction(CCFadeTo::create(0.16f, 150));',
        '''m_scrim->runAction(CCFadeTo::create(0.16f * uiMotion(),
            static_cast<GLubyte>(255.f * static_cast<float>(Mod::get()->getSettingValue<double>("ui-dim")))));''',
        'backdrop dim control')
    source = replace_once(source,
        'm_deck->runAction(CCEaseBackOut::create(CCScaleTo::create(0.3f, m_deckScale)));',
        'm_deck->runAction(CCEaseOut::create(CCScaleTo::create(0.25f * uiMotion(), m_deckScale), 2.f));',
        'subtle Apple-style open motion')
    source = replace_once(source,
        'CCScaleTo::create(0.12f, m_deckScale * 0.96f)',
        'CCScaleTo::create(0.12f * uiMotion(), m_deckScale * 0.96f)', 'close scale motion')
    source = replace_once(source,
        'CCFadeTo::create(0.12f, 0)',
        'CCFadeTo::create(0.12f * uiMotion(), 0)', 'close dim motion')
    source = replace_once(source,
        'CCDelayTime::create(0.16f)',
        'CCDelayTime::create(0.16f * uiMotion())', 'close input delay')

    # All checks succeeded; only now write updated files and retain backups.
    outinfo = json.dumps(info, ensure_ascii=False, indent=2) + '\n'
    (root / 'src' / 'main.cpp.before-slate').write_text(src.read_text(encoding='utf-8'), encoding='utf-8')
    (root / 'mod.json.before-slate').write_text(mod.read_text(encoding='utf-8'), encoding='utf-8')
    src.write_text(source, encoding='utf-8')
    mod.write_text(outinfo, encoding='utf-8')
    print('Slate patch applied successfully to source. Backups written. Now build with Geode.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path, help='path to downloaded Afterflow source folder')
    args = parser.parse_args()
    patch(args.source.resolve())
