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

    void AfterflowOverlay::renderV3() {
        if (!m_v3Root) return;
        auto* mod = Mod::get();
        bool enabled = state.isEnabled && mod->getSettingValue<bool>("input-enabled")
            && !mod->getSavedValue<bool>("aurora-bypass", false);
        int palette = std::clamp(mod->getSavedValue<int>("v3-accent-index", 0),0,5);
        static int const accentHex[] = {0x9991F4,0x78ADFA,0x62D7AE,0xF1B97B,0xF6A5BE,0xD5D6E1};
        ccColor3B accent=hexColor(accentHex[palette]);
        ccColor3B white=hexColor(0xF5F5F8);
        ccColor3B dim=hexColor(0xA9ACB8);
        ccColor3B muted=hexColor(0x747889);
        ccColor3B card=hexColor(0x20222B);
        ccColor3B lightCard=hexColor(0x292B36);
        std::string key=fmt::format("{}:{}:{}:{}:{}:{}:{}:{}:{:.2f}:{}:{}:{}:{}",
            m_activeTab, state.stageIndex, state.ticksAllModes, state.ticksWaveMode,
            enabled, palette, g_aurora.inputCount, g_aurora.queuedCount,
            mod->getSettingValue<double>("input-strength"),
            mod->getSettingValue<bool>("input-presses"),
            mod->getSettingValue<bool>("input-releases"),
            mod->getSettingValue<bool>("aurora-reduce-motion"),
            stageTotalCount());
        if(m_activeTab==2)for(int i=0;i<8;++i)
            key += mod->getSettingValue<bool>(fmt::format("input-{}",AURORA_MODES[i])) ? "1":"0";
        if(key==m_v3Signature)return;
        m_v3Signature=key;
        m_v3Root->removeAllChildrenWithCleanup(true);
        auto* d=makeDrawNode();
        m_v3Root->addChild(d,0);
        auto panel=[&](CCRect r,float radius,ccColor3B color,int border=0) {
            drawCurvedRect(d,r,radius,color4(color,255),
                color4(255,255,255,border),border?0.8f:0.f);
        };
        auto label=[&](std::string const& text,float x,float y,float scale,ccColor3B c,
                       bool heavy=false,float maxWidth=0.f) {
            auto* l=makeLabel(text,heavy,scale,c);
            if(!l)return;
            if(maxWidth>0.f)fitLabelToWidth(l,maxWidth);
            l->setAnchorPoint(CCPoint(0.f,0.5f));
            l->setPosition(CCPoint(x,y));
            m_v3Root->addChild(l,1);
        };
        auto centered=[&](std::string const& text,CCRect r,float scale,
                          ccColor3B c,bool heavy=false) {
            auto* l=makeLabel(text,heavy,scale,c);
            if(!l)return;
            fitLabelToWidth(l,r.size.width-10.f);
            l->setPosition(CCPoint(r.getMidX(),r.getMidY()));
            m_v3Root->addChild(l,1);
        };
        auto button=[&](CCRect r,std::string const& text,bool active=false,float size=.68f) {
            panel(r,9,active ? hexColor(0x333244) : card,active?0:9);
            centered(text,r,size,active?white:dim);
        };
        // Intentionally opaque: the UI must stay readable over bright GD levels.
        panel(CCRect(0,0,DECK_WIDTH,DECK_HEIGHT),19,hexColor(0x14151B),9);
        panel(CCRect(1,1,174,DECK_HEIGHT-2),18,hexColor(0x101116));
        d->drawSegment(CCPoint(175,20),CCPoint(175,440),.5f,color4(255,255,255,17));
        panel(CCRect(26,400,31,31),9,hexColor(0x3C3652));
        centered("A",CCRect(26,400,31,31),.85f,accent,true);
        label("afterflow",69,416,.92f,white,true,97);
        label("WORKSPACE",27,369,.53f,muted);
        static char const* titles[]={"Activity","Stages","Controls","Insights","Commands","Appearance"};
        static char const* nums[]={"01","02","03","04","05","06"};
        for(int i=0;i<6;++i) {
            CCRect r(18,323-i*47,151,41);
            if(m_activeTab==i)panel(r,10,lightCard);
            label(nums[i],29,r.getMidY(),.58f,m_activeTab==i?accent:muted);
            label(titles[i],56,r.getMidY(),.78f,m_activeTab==i?white:dim,true,106);
        }
        d->drawSegment(CCPoint(26,65),CCPoint(155,65),.5f,color4(255,255,255,20));
        label("ENGINE STATUS",28,49,.53f,muted);
        label(enabled?"CORRECTION ON":"BYPASSED",28,31,.71f,
            enabled?hexColor(0x80DEB5):dim,true);
        label(titles[m_activeTab],198,418,1.12f,white,true,280);
        panel(CCRect(535,402,106,33),10,enabled?hexColor(0x253E36):hexColor(0x2B2C34));
        centered(enabled?"Enabled":"Disabled",CCRect(535,402,106,33),.74f,
            enabled?hexColor(0x9DE3C0):dim);
        button(CCRect(655,402,31,33),"x");
        if(m_activeTab==1) {
            label("Choose a preset or customize a timing window.",198,383,.69f,dim,false,455);
            panel(CCRect(194,212,484,152),14,card,8);
            label("SELECTED PRESET",212,342,.53f,muted);
            label(stageTitleAt(state.stageIndex),212,319,1.08f,white,true,225);
            label(fmt::format("{:02} / {:02}",state.stageIndex+1,stageTotalCount()),
                400,323,.68f,dim);
            button(CCRect(495,314,30,29),"<");
            button(CCRect(529,314,30,29),">");
            button(CCRect(568,314,85,29),"+ Custom",false,.65f);
            int page=(state.stageIndex/10)*10;
            for(int j=0;j<10;++j) {
                int i=page+j;
                if(i>=stageTotalCount())break;
                CCRect r(209+j%5*91,227+(1-j/5)*35,85,29);
                bool sel=(i==state.stageIndex);
                panel(r,8,sel?hexColor(0x383345):hexColor(0x2B2C34));
                if(sel)panel(CCRect(r.getMinX(),r.getMinY()+3,3,r.size.height-6),1,accent);
                centered(stageLabelAt(i),r,.65f,sel?white:dim);
            }
            label("PREDICTION WINDOWS",198,188,.55f,muted);
            for(int i=0;i<2;++i) {
                float x=i?442.f:194.f;
                panel(CCRect(x,51,235,119),13,card,8);
                label(i?"Wave":"All gamemodes",x+17,143,.72f,dim);
                int val=state.isEnabled?(i?state.ticksWaveMode:state.ticksAllModes):0;
                label(fmt::format("{} ticks",val),x+17,105,1.13f,white,true,123);
                panel(CCRect(x+17,71,201,7),3,hexColor(0x393B46));
                float denom=static_cast<float>(std::max(40,std::max(state.ticksAllModes,state.ticksWaveMode)));
                float w=std::clamp(201.f*val/denom,0.f,201.f);
                if(w>1.f)panel(CCRect(x+17,71,w,7),3,accent);
                if(customStageFor(state.stageIndex)) {
                    button(CCRect(x+152,85,30,26),"-");
                    button(CCRect(x+190,85,30,26),"+");
                }
            }
        } else if(m_activeTab==2) {
            label("Tune your input engine in one place.",198,383,.68f,dim);
            panel(CCRect(200,301,466,65),13,card,8);
            label("Input correction",218,342,.81f,white,true);
            label("Apply predicted input timing",218,318,.64f,dim);
            centered(enabled?"ON":"OFF",CCRect(585,315,61,34),.87f,
                enabled?hexColor(0x82DDB5):dim,true);
            panel(CCRect(200,219,466,67),13,card,8);
            label("Window strength",218,260,.81f,white,true);
            label(fmt::format("{:.2f}x",mod->getSettingValue<double>("input-strength")),
                458,251,.91f,accent,true);
            button(CCRect(590,232,36,30),"-");
            button(CCRect(631,232,36,30),"+");
            label("TIMING ACTIONS",204,196,.56f,muted);
            button(CCRect(420,168,114,35),
                mod->getSettingValue<bool>("input-presses")?"Press ON":"Press OFF",
                mod->getSettingValue<bool>("input-presses"),.68f);
            button(CCRect(547,168,114,35),
                mod->getSettingValue<bool>("input-releases")?"Release ON":"Release OFF",
                mod->getSettingValue<bool>("input-releases"),.68f);
            label("GAMEMODES",204,149,.54f,muted);
            static char const* modes[]={"Cube","Ship","Ball","UFO","Wave","Robot","Spider","Swing"};
            for(int i=0;i<8;++i) {
                CCRect r(205+i%4*115,107-i/4*47,108,38);
                bool ok=mod->getSettingValue<bool>(fmt::format("input-{}",AURORA_MODES[i]));
                panel(r,9,ok?lightCard:card,ok?0:8);
                centered(modes[i],r,.72f,ok?white:muted,true);
                if(ok)d->drawCircle(CCPoint(r.getMinX()+10,r.getMaxY()-9),2.3f,
                    color4(accent),0.f,color4(0,0,0,0),12);
            }
        } else if(m_activeTab==0) {
            label("A clean overview of the current input session.",198,382,.68f,dim);
            panel(CCRect(194,52,484,325),14,card,8);
            label("LIVE SESSION",214,351,.56f,muted);
            button(CCRect(544,344,118,34),"Copy log");
            label(fmt::format("{} inputs",g_aurora.inputCount),215,304,1.04f,white,true,196);
            label(fmt::format("{} queued",g_aurora.queuedCount),440,304,1.04f,accent,true,205);
            d->drawSegment(CCPoint(214,271),CCPoint(659,271),.5f,color4(255,255,255,18));
            label("RECENT EVENTS",215,245,.55f,muted);
            for(int i=0;i<5;++i) {
                if(m_activityLines[i])label(m_activityLines[i]->getString(),
                    217,217-i*34,.69f,i==0?white:dim,false,435);
            }
        } else if(m_activeTab==3) {
            label("Actual queued timing events; not predicted survival rates.",198,382,.68f,dim);
            for(int i=0;i<3;++i) {
                float x=194+i*164;
                panel(CCRect(x,262,153,107),13,card,8);
                label(i==0?"Inputs":i==1?"Queued":"Average delay",x+15,338,.66f,dim);
                std::string number=i==0?fmt::format("{}",g_aurora.inputCount):
                    i==1?fmt::format("{}",g_aurora.queuedCount):
                    fmt::format("{:.1f} t",g_aurora.queuedCount?
                        (double)g_aurora.queuedTickSum/g_aurora.queuedCount:0.);
                label(number,x+15,296,1.1f,i==1?accent:white,true,127);
            }
            panel(CCRect(194,171,484,76),13,card,8);
            label("CORRECTION DELAY HISTORY",211,224,.55f,muted);
            int n=std::min((int)g_aurora.history.size(),32);
            for(int i=0;i<n;++i) {
                auto const& e=g_aurora.history[g_aurora.history.size()-n+i];
                float h=std::clamp((float)e.ticks/32.f*36.f,3.f,36.f);
                float x=215.f+i*13.75f;
                d->drawSegment(CCPoint(x,186),CCPoint(x,186+h),3.7f,
                    color4(e.press?accent:hexColor(0x7DCBD8),190));
            }
            static char const* actions[]={"Balanced","Adaptive","Wide","Copy CSV","Save preset","Load preset"};
            for(int i=0;i<6;++i)
                button(CCRect(206+i%3*155,62+(1-i/3)*51,146,40),actions[i]);
        } else if(m_activeTab==4) {
            label("Useful actions, without hunting through settings.",198,382,.69f,dim);
            static char const* commands[]={
                "Toggle correction","Emergency bypass","Adaptive timing","Mini HUD",
                "Copy session CSV","Clear statistics","Save level profile","Load level profile"
            };
            for(int i=0;i<8;++i) {
                CCRect r(203+i%2*235,277-i/2*63,220,54);
                panel(r,11,card,8);
                label(commands[i],r.getMinX()+17,r.getMidY(),.73f,white,true,184);
            }
        } else {
            label("Customize accent colors without visual clutter.",198,382,.68f,dim);
            label("ACCENT COLORS",205,342,.56f,muted);
            static char const* accents[]={"Lavender","Sky","Mint","Sand","Rose","Mono"};
            for(int i=0;i<6;++i) {
                CCRect r(207+i%3*151,221-i/3*72,142,56);
                panel(r,11,palette==i?lightCard:card,palette==i?0:8);
                d->drawCircle(CCPoint(r.getMinX()+22,r.getMidY()),7.f,
                    color4(hexColor(accentHex[i])),0.f,color4(0,0,0,0),16);
                label(accents[i],r.getMinX()+38,r.getMidY(),.66f,palette==i?white:dim);
            }
            label("MOTION",205,139,.55f,muted);
            bool reduced=mod->getSettingValue<bool>("aurora-reduce-motion");
            button(CCRect(204,76,462,48),
                reduced?"Reduced motion   •   ON":"Reduced motion   •   OFF",reduced,.76f);
            label("Original Afterflow by sevend and contributors",204,43,.55f,muted);
        }
    }

'''
