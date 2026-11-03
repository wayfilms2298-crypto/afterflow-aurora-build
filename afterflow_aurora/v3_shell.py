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

    int AfterflowOverlay::v3Hit(CCPoint p) const {
        if (!CCRect(0.f,0.f,DECK_WIDTH,DECK_HEIGHT).containsPoint(p)) return 900;
        if (CCRect(655,400,30,34).containsPoint(p)) return 900;
        if (CCRect(535,404,106,30).containsPoint(p)) return 901;
        for(int i=0;i<6;++i)
            if(CCRect(18,323-i*47,151,41).containsPoint(p)) return 100+i;
        if(m_activeTab==1) {
            int page=(state.stageIndex/10)*10;
            for(int j=0;j<10;++j) {
                int i=page+j;
                if(i<stageTotalCount() &&
                    CCRect(209+j%5*91,227+(1-j/5)*35,85,29).containsPoint(p)) return 200+i;
            }
            if(CCRect(568,314,85,29).containsPoint(p)) return 281;
            if(CCRect(495,314,30,29).containsPoint(p)) return 290;
            if(CCRect(529,314,30,29).containsPoint(p)) return 291;
            if(customStageFor(state.stageIndex))
                for(int i=0;i<2;++i) {
                    float x=i?442.f:194.f;
                    if(CCRect(x+152,85,30,26).containsPoint(p))return 300+i*2;
                    if(CCRect(x+190,85,30,26).containsPoint(p))return 301+i*2;
                }
        }
        if(m_activeTab==2) {
            if(CCRect(202,301,463,64).containsPoint(p))return 420;
            if(CCRect(590,232,36,30).containsPoint(p))return 430;
            if(CCRect(631,232,36,30).containsPoint(p))return 431;
            if(CCRect(420,168,114,35).containsPoint(p))return 421;
            if(CCRect(547,168,114,35).containsPoint(p))return 422;
            for(int i=0;i<8;++i)
                if(CCRect(205+i%4*115,107-i/4*47,108,38).containsPoint(p))return 400+i;
        }
        if(m_activeTab==3)for(int i=0;i<6;++i)
            if(CCRect(206+i%3*155,62+(1-i/3)*51,146,40).containsPoint(p))return 600+i;
        if(m_activeTab==4)for(int i=0;i<8;++i)
            if(CCRect(203+i%2*235,277-i/2*63,220,54).containsPoint(p))return 500+i;
        if(m_activeTab==5) {
            for(int i=0;i<6;++i)
                if(CCRect(207+i%3*151,221-i/3*72,142,56).containsPoint(p))return 700+i;
            if(CCRect(204,76,462,48).containsPoint(p))return 710;
        }
        if(m_activeTab==0&&CCRect(544,344,118,34).containsPoint(p))return 800;
        return -1;
    }

    void AfterflowOverlay::v3Action(int id) {
        auto* mod=Mod::get();
        if(id==900){closePanel();return;}
        if(id==901||id==420) {
            mod->setSettingValue<bool>("input-enabled",!mod->getSettingValue<bool>("input-enabled"));
            resetPending();
        } else if(id>=100&&id<106) {
            m_activeTab=id-100;applyTab();
        } else if(id>=200&&id<200+stageTotalCount()) {
            setStageIndex(id-200);
        } else if(id==281) {
            performTarget(HitTarget::StageAdd);
        } else if(id==290) {
            setStageIndex((state.stageIndex+stageTotalCount()-1)%stageTotalCount());
        } else if(id==291) {
            setStageIndex((state.stageIndex+1)%stageTotalCount());
        } else if(id>=300&&id<304) {
            if(auto* custom=customStageFor(state.stageIndex)) {
                int row=(id-300)/2,step=(id%2)?1:-1;
                int& val=row?custom->ticksWave:custom->ticksAll;
                val=clampCustomTicks(val+step);
                saveCustomStages();
                setStageIndex(state.stageIndex);
            }
        } else if(id>=400&&id<408) {
            auto key=fmt::format("input-{}",AURORA_MODES[id-400]);
            mod->setSettingValue<bool>(key,!mod->getSettingValue<bool>(key));
            resetPending();
        } else if(id==421||id==422) {
            auto key=id==421?"input-presses":"input-releases";
            mod->setSettingValue<bool>(key,!mod->getSettingValue<bool>(key));
            resetPending();
        } else if(id==430||id==431) {
            double prev=mod->getSettingValue<double>("input-strength");
            mod->setSettingValue<double>("input-strength",std::clamp(prev+(id==430?-.05:.05),.5,1.5));
            resetPending();
        } else if(id>=500&&id<508) {
            runAuroraCommand(id-500);
        } else if(id>=600&&id<606) {
            if(id<603)auroraApplyPreset(id-600);
            if(id==603)geode::utils::clipboard::write(auroraCSV().c_str());
            if(id==604)auroraSaveProfile(auroraProfileKey(1));
            if(id==605)auroraLoadProfile(auroraProfileKey(1));
        } else if(id>=700&&id<706) {
            mod->setSavedValue<int>("v3-accent-index",id-700);
            (void)mod->saveData();
        } else if(id==710) {
            mod->setSettingValue<bool>("aurora-reduce-motion",
                !mod->getSettingValue<bool>("aurora-reduce-motion"));
        } else if(id==800)copyLog();
        m_v3Signature.clear();
        refresh();
    }

