"""Native Aurora V3 sidebar UI over the existing functional engine."""
from slate_core import replace_once

def patch_string(src):
    def r(old,new,label):
        nonlocal src
        src=replace_once(src,old,new,"V3 "+label)
    r("        CCNodeRGBA* m_commandsPane = nullptr;",
      """        CCNodeRGBA* m_commandsPane = nullptr;
        CCNode* m_v3Root = nullptr;
        std::string m_v3Signature;
        int m_v3Pressed = -1;
        int v3Hit(CCPoint p) const;
        void v3Action(int id);
        void renderV3();""","class members")
    r("        m_commandsPane = nullptr;",
      """        m_commandsPane = nullptr;
        m_v3Root = nullptr;
        m_v3Signature.clear();
        m_v3Pressed = -1;""","reset")
    r("""        m_tabBar = makeDrawNode();
        m_deck->addChild(m_tabBar, 2);""",
      """        m_v3Root = CCNode::create();
        m_deck->addChild(m_v3Root, 800);
        m_tabBar = makeDrawNode();
        m_deck->addChild(m_tabBar, 2);""","overlay")
    r("""    void AfterflowOverlay::refresh() {
        if (!m_deck) {
            return;
        }""",
      """    void AfterflowOverlay::refresh() {
        if (!m_deck) {
            return;
        }
        renderV3();""","render")
    r("""    bool AfterflowOverlay::ccTouchBegan(CCTouch* touch, CCEvent*) {
        if (!touch) {
            return false;
        }""",
      """    bool AfterflowOverlay::ccTouchBegan(CCTouch* touch, CCEvent*) {
        if (!touch) {
            return false;
        }
        if (m_isOpen && m_v3Root) {
            m_v3Pressed = v3Hit(m_deck->convertToNodeSpace(touch->getLocation()));
            return true;
        }""","touch began")
    r("""    void AfterflowOverlay::ccTouchMoved(CCTouch* touch, CCEvent*) {
        if (!touch) {
            return;
        }""",
      """    void AfterflowOverlay::ccTouchMoved(CCTouch* touch, CCEvent*) {
        if (!touch) {
            return;
        }
        if (m_isOpen && m_v3Root) return;""","touch moved")
    r("""    void AfterflowOverlay::ccTouchEnded(CCTouch* touch, CCEvent*) {
        if (!touch) {
            return;
        }""",
      """    void AfterflowOverlay::ccTouchEnded(CCTouch* touch, CCEvent*) {
        if (!touch) {
            return;
        }
        if (m_isOpen && m_v3Root) {
            int id = v3Hit(m_deck->convertToNodeSpace(touch->getLocation()));
            int held = m_v3Pressed;
            m_v3Pressed = -1;
            if (held >= 0 && held == id) v3Action(id);
            return;
        }""","touch ended")
    r("""    void AfterflowOverlay::ccTouchCancelled(CCTouch*, CCEvent*) {
        if (m_draggingSlider) {""",
      """    void AfterflowOverlay::ccTouchCancelled(CCTouch*, CCEvent*) {
        m_v3Pressed = -1;
        if (m_draggingSlider) {""","cancel")
    r("""        if (m_tutorialStep < 0 && !Mod::get()->getSavedValue<bool>(TUTORIAL_DONE_KEY, false)) {
            startTutorial();
        }""",
      """        // Old three-tab tutorial is not compatible with V3 navigation.""","tour")
    r("float comfortableScale = std::min(fitScale, 0.94f);",
      "float comfortableScale = std::min(fitScale, 0.82f);","fit scale")
    r("    void AfterflowOverlay::copyLog() {",
      V3_CPP+"    void AfterflowOverlay::copyLog() {","native code")
    return src

V3_CPP = r'''
