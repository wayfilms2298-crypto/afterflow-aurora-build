"""Aurora V4: replace the legacy UI renderer with a retained native Cocos2d-x tree.

Runs *after* the stable engine, Slate, Aurora telemetry and V3 patches.
Gameplay prediction, mod settings, pause/input suppression and game hooks stay intact.
Every replacement is anchored; drift aborts compilation rather than silently shipping V3.
"""
from __future__ import annotations
from slate_core import replace_once
from v4_render import V4_HIT, V4_ACTION, V4_RENDER


def replace_definition(source: str, signature: str, replacement: str) -> str:
    if source.count(signature) != 1:
        raise RuntimeError(f"V4 expected exactly one method: {signature}")
    a = source.index(signature)
    brace = source.index("{", a)  # Include the method opening brace in depth accounting
    depth = 0
    quote = ""
    escaped = False
    line_comment = False
    block_comment = False
    k = brace
    while k < len(source):
        ch = source[k]
        nxt = source[k + 1] if k + 1 < len(source) else ""
        if line_comment:
            if ch == "\n":
                line_comment = False
        elif block_comment:
            if ch == "*" and nxt == "/":
                block_comment = False
                k += 1
        elif quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = ""
        elif ch == "/" and nxt == "/":
            line_comment = True
            k += 1
        elif ch == "/" and nxt == "*":
            block_comment = True
            k += 1
        elif ch in "\"'":
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return source[:a] + replacement + source[k + 1:]
        k += 1
    raise RuntimeError(f"Unbalanced method: {signature}")


def patch_string(src: str) -> str:
    if "AURORA_V4_NATIVE_TREE" in src:
        raise RuntimeError("V4 already applied")
    src = replace_once(src,
        """        std::string m_v3Signature;""",
        """        // AURORA_V4_NATIVE_TREE: persistent sidebar, page, header and motion nodes.
        std::string m_v3Signature;
        CCNode* m_v4Chrome = nullptr;
        CCNodeRGBA* m_v4Page = nullptr;
        CCDrawNode* m_v4Indicator = nullptr;
        CCNode* m_v4Header = nullptr;
        CCLabelBMFont* m_v4StateLabel = nullptr;
        CCLabelBMFont* m_v4FooterLabel = nullptr;
        CCLabelBMFont* m_v4NavLabels[7] = {};
        int m_v4RenderedTab = -1;
        int m_v4Accent = 0;
        bool m_v4LastEnabled = false;
        void v4Notify(std::string const& message);
        void v4StrengthAt(float x);""",
        "class fields")

    old_begin = "    void AfterflowOverlay::buildDeck() {"
    a = src.index(old_begin)
    b = src.index("    void AfterflowOverlay::rebuildDeck()", a)
    old = src[a:b]
    reset_start = old.index("        // rebuildDeck() frees")
    reset_end = old.index("        ccColor3B surface = getUISurfaceColor();")
    resets = old[reset_start:reset_end]
    # Retain ALL pointer resets (including v3 pointers), but do NOT allocate any legacy
    # stage tabs, background draw nodes, controls, or fake/hidden setting cards.
    clean_build = """    void AfterflowOverlay::buildDeck() {
""" + resets + """
        m_v4Chrome = nullptr;
        m_v4Page = nullptr;
        m_v4Indicator = nullptr;
        m_v4Header = nullptr;
        m_v4StateLabel = nullptr;
        m_v4FooterLabel = nullptr;
        m_v4RenderedTab = -1;
        for (auto& label : m_v4NavLabels) label = nullptr;
        m_v3Root = CCNode::create();
        m_deck->addChild(m_v3Root, 1);
        applyTab();
    }
"""
    src = src[:a] + clean_build + src[b:]

    src = replace_definition(src, "    void AfterflowOverlay::applyTab() {",
      """    void AfterflowOverlay::applyTab() {
        m_activeTab = std::clamp(m_activeTab, 0, 6);
        m_v3Signature.clear();
    }""")
    src = replace_definition(src, "    void AfterflowOverlay::refresh() {",
      """    void AfterflowOverlay::refresh() {
        if (m_deck && m_v3Root) renderV3();
    }""")
    src = replace_definition(src, "    int AfterflowOverlay::v3Hit(CCPoint p) const {", V4_HIT)
    src = replace_definition(src, "    void AfterflowOverlay::v3Action(int id) {", V4_ACTION)
    src = replace_definition(src, "    void AfterflowOverlay::renderV3() {", V4_RENDER)
    # Match the new window size, not the full-screen legacy surface.
    src = replace_once(src, "float comfortableScale = std::min(fitScale, 0.82f);",
        "float comfortableScale = std::min(fitScale, 0.72f);", "compact layout")
    # No back-easing bounce; small scale delta and 190ms easing.
    src = replace_once(src, "m_deck->setScale(m_deckScale * 0.94f);",
        "m_deck->setScale(m_deckScale * 0.972f);", "opening scale")
    src = replace_once(src,
        "m_deck->runAction(CCEaseOut::create(CCScaleTo::create(0.36f * uiMotion(), m_deckScale), 3.2f));",
        "m_deck->runAction(CCEaseSineOut::create(CCScaleTo::create(0.19f * uiMotion(), m_deckScale)));",
        "opening easing")
    # Allow the slider to respond to actual dragging while keeping all events swallowed.
    src = replace_once(src,
        """        if (m_isOpen && m_v3Root) return;
        if (m_isDraggingLauncher)""",
        """        if (m_isOpen && m_v3Root) {
            if (m_v3Pressed == 432)
                v4StrengthAt(m_deck->convertToNodeSpace(touch->getLocation()).x);
            return;
        }
        if (m_isDraggingLauncher)""",
        "slider drag")
    src = replace_once(src,
        """            m_v3Pressed = v3Hit(m_deck->convertToNodeSpace(touch->getLocation()));
            return true;""",
        """            CCPoint point = m_deck->convertToNodeSpace(touch->getLocation());
            m_v3Pressed = v3Hit(point);
            if (m_v3Pressed == 432) v4StrengthAt(point.x);
            return true;""",
        "slider begin")
    return src
