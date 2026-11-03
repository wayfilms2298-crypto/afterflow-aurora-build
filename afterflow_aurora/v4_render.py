"""Source fragments for Aurora V4's compact, native Cocos2d-x interface."""

V4_HIT = r'''
    int AfterflowOverlay::v3Hit(CCPoint p) const {
        if (!CCRect(0.f,0.f,DECK_WIDTH,DECK_HEIGHT).containsPoint(p)) return 900;
        if (CCRect(656.f,402.f,30.f,30.f).containsPoint(p)) return 900;
        if (CCRect(572.f,402.f,75.f,30.f).containsPoint(p)) return 901;
        for(int i=0;i<7;++i)
            if(CCRect(16.f,326.f-i*43.f,151.f,38.f).containsPoint(p))return 100+i;
        if(m_activeTab==1) {
            if(CCRect(564.f,304.f,98.f,28.f).containsPoint(p))return 281;
            if(CCRect(494.f,304.f,29.f,28.f).containsPoint(p))return 290;
            if(CCRect(529.f,304.f,29.f,28.f).containsPoint(p))return 291;
            int page=(state.stageIndex/8)*8;
            for(int j=0;j<8;++j) {
                int i=page+j;
                if(i<stageTotalCount() &&
                    CCRect(212.f+j%4*113.f,213.f+(1-j/4)*34.f,106.f,29.f).containsPoint(p))
                    return 200+i;
            }
            if(customStageFor(state.stageIndex))for(int i=0;i<2;++i) {
                float x=i?445.f:205.f;
                if(CCRect(x+145.f,105.f,30.f,27.f).containsPoint(p))return 300+i*2;
                if(CCRect(x+182.f,105.f,30.f,27.f).containsPoint(p))return 301+i*2;
            }
        } else if(m_activeTab==2) {
            if(CCRect(609.f,318.f,42.f,26.f).containsPoint(p))return 420;
            if(CCRect(591.f,237.f,30.f,28.f).containsPoint(p))return 430;
            if(CCRect(631.f,237.f,30.f,28.f).containsPoint(p))return 431;
            if(CCRect(401.f,237.f,184.f,28.f).containsPoint(p))return 432;
            if(CCRect(481.f,179.f,83.f,30.f).containsPoint(p))return 421;
            if(CCRect(574.f,179.f,89.f,30.f).containsPoint(p))return 422;
            for(int i=0;i<8;++i) {
                if(CCRect(208.f+i%4*114.f,90.f-i/4*40.f,105.f,31.f).containsPoint(p))
                    return 400+i;
            }
        } else if(m_activeTab==3) {
            if(CCRect(538.f,73.f,126.f,32.f).containsPoint(p))return 603;
            if(CCRect(400.f,73.f,126.f,32.f).containsPoint(p))return 610;
        } else if(m_activeTab==4) {
            for(int i=0;i<8;++i)
                if(CCRect(203.f+i%2*239.f,260.f-i/2*60.f,226.f,48.f).containsPoint(p))
                    return 500+i;
        } else if(m_activeTab==5) {
            for(int i=0;i<3;++i) {
                float y=281.f-i*88.f;
                if(CCRect(520.f,y,68.f,32.f).containsPoint(p))return 620+i*2;
                if(CCRect(596.f,y,68.f,32.f).containsPoint(p))return 621+i*2;
            }
            for(int i=0;i<3;++i)
                if(CCRect(210.f+i*153.f,32.f,143.f,34.f).containsPoint(p))return 600+i;
        } else if(m_activeTab==6) {
            for(int i=0;i<6;++i)
                if(CCRect(205.f+i%3*154.f,220.f-i/3*57.f,145.f,46.f).containsPoint(p))
                    return 700+i;
            if(CCRect(542.f,93.f,120.f,37.f).containsPoint(p))return 710;
            if(CCRect(567.f,44.f,43.f,28.f).containsPoint(p))return 720;
            if(CCRect(617.f,44.f,43.f,28.f).containsPoint(p))return 721;
        }
        return -1;
    }

'''

V4_ACTION = r'''
    void AfterflowOverlay::v4Notify(std::string const& message) {
        if(!m_v3Root)return;
        auto* toast=makeLabel(message,false,.65f,hexColor(0xF1F2F8));
        if(!toast)return;
        auto* back=makeDrawNode();
        float w=std::max(132.f,toast->getContentSize().width*toast->getScale()+36.f);
        drawCurvedRect(back,CCRect(-w*.5f,-18.f,w,36.f),10.f,
            color4(47,50,66,245),color4(255,255,255,22),.8f);
        toast->setPosition(CCPoint(0,0));
        auto* host=CCNode::create();
        host->setPosition(CCPoint(444.f,42.f));
        host->addChild(back,0);
        host->addChild(toast,1);
        m_v3Root->addChild(host,99);
        toast->setOpacity(0);
        toast->runAction(CCSequence::create(
            CCFadeTo::create(.16f,255),
            CCDelayTime::create(1.35f),
            CCFadeTo::create(.25f,0),
            CallFuncExt::create([host]{host->removeFromParentAndCleanup(true);}),
            nullptr));
    }

    void AfterflowOverlay::v4StrengthAt(float x) {
        auto* mod=Mod::get();
        double next=std::clamp((double)((x-406.f)/170.f)*1.0+.5,.5,1.5);
        next=std::round(next*20.)/20.;
        if(std::abs(mod->getSettingValue<double>("input-strength")-next)>.001) {
            mod->setSettingValue<double>("input-strength",next);
            resetPending();
            m_v3Signature.clear();
            refresh();
        }
    }

    void AfterflowOverlay::v3Action(int id) {
        auto* mod=Mod::get();
        if(id==900){closePanel();return;}
        if(id==901||id==420) {
            mod->setSettingValue<bool>("input-enabled",
                !mod->getSettingValue<bool>("input-enabled"));
            resetPending();
        } else if(id>=100&&id<=106) {
            if(m_activeTab!=id-100) {
                m_activeTab=id-100;
                applyTab();
            }
        } else if(id>=200&&id<200+stageTotalCount()) {
            setStageIndex(id-200);
        } else if(id==281) {
            performTarget(HitTarget::StageAdd);
            return;
        } else if(id==290) {
            setStageIndex((state.stageIndex+stageTotalCount()-1)%stageTotalCount());
        } else if(id==291) {
            setStageIndex((state.stageIndex+1)%stageTotalCount());
        } else if(id>=300&&id<=303) {
            if(auto* custom=customStageFor(state.stageIndex)) {
                int row=(id-300)/2;
                int& ticks=row?custom->ticksWave:custom->ticksAll;
                ticks=clampCustomTicks(ticks+((id&1)?1:-1));
                saveCustomStages();setStageIndex(state.stageIndex);
            }
        } else if(id>=400&&id<=407) {
            std::string key=fmt::format("input-{}",AURORA_MODES[id-400]);
            mod->setSettingValue<bool>(key,!mod->getSettingValue<bool>(key));
            resetPending();
        } else if(id==421||id==422) {
            char const* key=id==421?"input-presses":"input-releases";
            mod->setSettingValue<bool>(key,!mod->getSettingValue<bool>(key));
            resetPending();
        } else if(id==430||id==431) {
            double strength=mod->getSettingValue<double>("input-strength");
            mod->setSettingValue<double>("input-strength",
                std::clamp(strength+(id==430?-.05:.05),.5,1.5));
            resetPending();
        } else if(id>=500&&id<=507) {
            runAuroraCommand(id-500);
            if(id==504)v4Notify("Session CSV copied");
            if(id==506)v4Notify("Level profile saved");
            if(id==507)v4Notify("Level profile loaded");
        } else if(id==603) {
            geode::utils::clipboard::write(auroraCSV().c_str());
            v4Notify("Session CSV copied");
        } else if(id==610) {
            g_aurora.clear();v4Notify("Statistics cleared");
        } else if(id>=620&&id<=625) {
            int slot=(id-620)/2+1;
            if(id%2==0) {auroraSaveProfile(auroraProfileKey(slot));v4Notify("Preset saved");}
            else {bool ok=auroraLoadProfile(auroraProfileKey(slot));v4Notify(ok?"Preset loaded":"Slot is empty");}
        } else if(id>=600&&id<=602) {
            auroraApplyPreset(id-600);
            v4Notify("Timing preset applied");
        } else if(id>=700&&id<=705) {
            mod->setSavedValue<int>("v3-accent-index",id-700);
            (void)mod->saveData();
        } else if(id==710) {
            mod->setSettingValue<bool>("aurora-reduce-motion",
                !mod->getSettingValue<bool>("aurora-reduce-motion"));
        } else if(id==720||id==721) {
            double current=mod->getSettingValue<double>("ui-panel-scale");
            mod->setSettingValue<double>("ui-panel-scale",
                std::clamp(current+(id==720?-.05:.05),.4,1.3));
            layout();
        }
        m_v3Signature.clear();
        refresh();
    }

'''

V4_RENDER = r'''
    void AfterflowOverlay::renderV3() {
        if(!m_v3Root)return;
        auto* mod=Mod::get();
        m_activeTab=std::clamp(m_activeTab,0,6);
        bool engine=state.isEnabled && mod->getSettingValue<bool>("input-enabled")
            && !mod->getSavedValue<bool>("aurora-bypass",false);
        int palette=std::clamp(mod->getSavedValue<int>("v3-accent-index",0),0,5);
        static int const paletteHex[]={0x9B93EF,0x79B2FF,0x68D2B6,0xE9B882,0xEBA5C2,0xCED4E1};
        ccColor3B accent=hexColor(paletteHex[palette]);
        ccColor3B white=hexColor(0xF4F4F8),secondary=hexColor(0xB2B5C4);
        ccColor3B muted=hexColor(0x848998),card=hexColor(0x1D2029);
        ccColor3B active=hexColor(0x2B2E3A),surface=hexColor(0x111319);

        auto line=[&](CCDrawNode* d,float x,float y,float x2,float y2,int alpha=20) {
            d->drawSegment(CCPoint(x,y),CCPoint(x2,y2),.5f,color4(255,255,255,alpha));
        };
        auto rect=[&](CCDrawNode* d,CCRect box,float radius,ccColor3B color,int outline=0) {
            drawCurvedRect(d,box,radius,color4(color),color4(255,255,255,outline),
                outline?.65f:0.f);
        };
        auto title=[&](CCNode* parent,std::string const& value,float x,float y,
                       float scale,ccColor3B color,bool heavy=false,float limit=0.f) -> CCLabelBMFont* {
            auto* label=makeLabel(value,heavy,scale,color);
            if(!label)return nullptr;
            if(limit>0.f)fitLabelToWidth(label,limit);
            label->setAnchorPoint(CCPoint(0.f,.5f));
            label->setPosition(CCPoint(x,y));
            parent->addChild(label,2);
            return label;
        };
        auto centered=[&](CCNode* parent,std::string const& value,CCRect r,
                          float scale,ccColor3B color,bool heavy=false) -> CCLabelBMFont* {
            auto* label=makeLabel(value,heavy,scale,color);
            if(!label)return nullptr;
            fitLabelToWidth(label,r.size.width-12.f);
            label->setPosition(CCPoint(r.getMidX(),r.getMidY()));
            parent->addChild(label,3);
            return label;
        };

        // Palette changes rebuild only static chrome; normal data updates retain it.
        if(m_v4Chrome && m_v4Accent!=palette) {
            m_v4Chrome->removeFromParentAndCleanup(true);
            m_v4Chrome=nullptr;
            m_v4Indicator=nullptr;
            m_v4StateLabel=nullptr;
            m_v4FooterLabel=nullptr;
            for(auto& label:m_v4NavLabels)label=nullptr;
            m_v4RenderedTab=-1;
        }
        static char const* tabs[]={"Activity","Stages","Controls","Insights","Commands","Presets","Appearance"};
        static char const* tabIds[]={"01","02","03","04","05","06","07"};
        if(!m_v4Chrome) {
            m_v4Accent=palette;
            m_v4Chrome=CCNode::create();
            m_v3Root->addChild(m_v4Chrome,0);
            auto* back=makeDrawNode();
            m_v4Chrome->addChild(back,0);
            rect(back,CCRect(0,0,DECK_WIDTH,DECK_HEIGHT),17,surface,12);
            rect(back,CCRect(1,1,174,DECK_HEIGHT-2),16,hexColor(0x0D0F15));
            line(back,174,18,174,442,24);
            // The brand mark is a monogram so there are no pixelated UI assets.
            rect(back,CCRect(24,401,31,31),8,hexColor(0x353147));
            centered(m_v4Chrome,"A",CCRect(24,401,31,31),.76f,accent,true);
            title(m_v4Chrome,"afterflow",65,416,.87f,white,true,103);
            title(m_v4Chrome,"WORKSPACE",26,375,.53f,muted);
            for(int i=0;i<7;++i) {
                CCRect slot(16,326.f-i*43.f,151,38);
                title(m_v4Chrome,tabIds[i],30,slot.getMidY(),.50f,muted,false,23);
                m_v4NavLabels[i]=title(m_v4Chrome,tabs[i],55,slot.getMidY(),
                    .75f,secondary,true,110);
            }
            m_v4Indicator=makeDrawNode();
            rect(m_v4Indicator,CCRect(0,0,3,27),1.5f,accent);
            m_v4Chrome->addChild(m_v4Indicator,5);
            line(back,25,59,155,59,22);
            title(m_v4Chrome,"ENGINE",28,43,.51f,muted);
            m_v4FooterLabel=title(m_v4Chrome,"READY",28,26,.69f,white,true,115);
            // Status is intentionally separate from the enable/disable action.
            m_v4StateLabel=centered(m_v4Chrome,"Enabled",CCRect(572,402,75,30),
                .62f,accent);
            title(m_v4Chrome,"AURORA",494,417,.49f,muted,true,64);
            rect(back,CCRect(572,402,75,30),9,card,10);
            rect(back,CCRect(656,402,30,30),9,card,10);
            centered(m_v4Chrome,"x",CCRect(656,402,30,30),.66f,secondary);
        }

        if(m_v4FooterLabel) {
            m_v4FooterLabel->setString(engine?"ENGINE ACTIVE":"BYPASSED");
            m_v4FooterLabel->setColor(engine?hexColor(0x8BD6AE):secondary);
        }
        if(m_v4StateLabel) {
            m_v4StateLabel->setString(engine?"Enabled":"Disabled");
            m_v4StateLabel->setColor(engine?hexColor(0x8BD6AE):secondary);
        }
        for(int i=0;i<7;++i)if(auto* item=m_v4NavLabels[i]) {
            item->setColor(i==m_activeTab?white:secondary);
            item->setOpacity(i==m_activeTab?255:185);
        }
        if(m_v4Indicator && m_v4RenderedTab!=m_activeTab) {
            float y=331.f-m_activeTab*43.f;
            m_v4Indicator->stopAllActions();
            if(m_v4RenderedTab<0 || mod->getSettingValue<bool>("aurora-reduce-motion")) {
                m_v4Indicator->setPosition(CCPoint(18,y));
            } else {
                m_v4Indicator->runAction(CCEaseSineOut::create(
                    CCMoveTo::create(.22f*uiMotion(),CCPoint(18,y))));
            }
        }

        // Only refresh the active page when its data changed. Static navigation is retained.
        std::string signature=fmt::format("{}:{}:{}:{}:{}:{}:{}:{}:{:.2f}:{}:{}:{}",
            m_activeTab,palette,engine,state.stageIndex,state.ticksAllModes,
            state.ticksWaveMode,g_aurora.inputCount,g_aurora.queuedCount,
            mod->getSettingValue<double>("input-strength"),
            mod->getSettingValue<bool>("input-presses"),
            mod->getSettingValue<bool>("input-releases"),
            mod->getSettingValue<bool>("aurora-reduce-motion"));
        if(m_activeTab==2)
            for(int i=0;i<8;++i)
                signature+=mod->getSettingValue<bool>(fmt::format("input-{}",AURORA_MODES[i]))?"1":"0";
        if(signature==m_v3Signature && m_v4Page)return;
        m_v3Signature=signature;
        int previousTab=m_v4RenderedTab;
        m_v4RenderedTab=m_activeTab;
        if(m_v4Page)m_v4Page->removeFromParentAndCleanup(true);
        m_v4Page=CCNodeRGBA::create();
        m_v4Page->setCascadeOpacityEnabled(true);
        m_v3Root->addChild(m_v4Page,1);
        auto* shape=makeDrawNode();
        m_v4Page->addChild(shape,0);
        auto t=[&](std::string const& s,float x,float y,float scale,ccColor3B c,
                   bool bold=false,float limit=0.f) {
            return title(m_v4Page,s,x,y,scale,c,bold,limit);
        };
        auto b=[&](CCRect r,std::string const& s,bool chosen=false,float scale=.64f) {
            rect(shape,r,9,chosen?active:card,chosen?0:9);
            centered(m_v4Page,s,r,scale,chosen?white:secondary);
        };
        auto section=[&](std::string const& s,float y) {t(s,203,y,.51f,muted,true);};
        t(tabs[m_activeTab],203,418,1.06f,white,true,325);

        if(m_activeTab==0) {
            t("Overview of your current input session.",204,383,.67f,secondary);
            for(int i=0;i<3;++i) {
                float x=203.f+i*160.f;
                rect(shape,CCRect(x,281,151,76),12,card,11);
                t(i==0?"INPUTS":i==1?"QUEUED":"AVG DELAY",x+14,335,.53f,muted,true);
                std::string val=i==0?fmt::format("{}",g_aurora.inputCount):
                    i==1?fmt::format("{}",g_aurora.queuedCount):
                    fmt::format("{:.1f}t",g_aurora.queuedCount?
                        (double)g_aurora.queuedTickSum/g_aurora.queuedCount:0.);
                t(val,x+14,308,1.0f,i==1?accent:white,true,122);
            }
            rect(shape,CCRect(203,161,471,108),12,card,9);
            section("RECENT INPUT CORRECTIONS",246);
            int n=std::min((int)g_aurora.history.size(),27);
            for(int i=0;i<n;++i) {
                auto const& e=g_aurora.history[g_aurora.history.size()-n+i];
                float h=std::clamp(e.ticks/32.f*53.f,3.f,53.f);
                float x=224.f+i*15.5f;
                shape->drawSegment(CCPoint(x,185),CCPoint(x,185+h),3.f,
                    color4(e.press?accent:hexColor(0x6ECBC8),220));
            }
            t(n?"Press and release adjustments":"No queued adjustments in this session",
                222,172,.56f,muted,false,415);
            section("SESSION DETAILS",141);
            rect(shape,CCRect(203,64,471,66),12,card,9);
            t("Corrections are recorded locally, not sent anywhere.",218,108,.65f,secondary,false,440);
            t("Measured queue events — no unverified accuracy claims.",218,84,.56f,muted,false,440);
        } else if(m_activeTab==1) {
            t("Select a timing stage. Use Custom to edit the input window.",204,383,.66f,secondary,false,460);
            rect(shape,CCRect(203,280,471,76),12,card,10);
            section("CURRENT STAGE",337);
            t(stageTitleAt(state.stageIndex),218,309,1.02f,white,true,235);
            t(fmt::format("{:02} / {:02}",state.stageIndex+1,stageTotalCount()),
                419,310,.64f,secondary);
            b(CCRect(494,304,29,28),"<");
            b(CCRect(529,304,29,28),">");
            b(CCRect(564,304,98,28),"+ Custom",false,.62f);
            int page=(state.stageIndex/8)*8;
            for(int j=0;j<8;++j) {
                int i=page+j;
                if(i>=stageTotalCount())break;
                CCRect rr(212.f+j%4*113.f,213.f+(1-j/4)*34.f,106.f,29.f);
                b(rr,stageLabelAt(i),i==state.stageIndex,.64f);
                if(i==state.stageIndex)
                    rect(shape,CCRect(rr.getMinX()+5,rr.getMinY()+5,3,rr.size.height-10),1.5,accent);
            }
            section("PREDICTION WINDOWS",192);
            for(int row=0;row<2;++row) {
                float x=row?444.f:203.f;
                rect(shape,CCRect(x,66,231,111),12,card,10);
                t(row?"WAVE":"ALL GAMEMODES",x+14,154,.52f,muted,true);
                int ticks=state.isEnabled?(row?state.ticksWaveMode:state.ticksAllModes):0;
                t(fmt::format("{} ticks",ticks),x+14,121,1.02f,white,true,126);
                rect(shape,CCRect(x+14,87,203,6),3,hexColor(0x3C404F));
                int maxTicks=std::max({40,state.ticksAllModes,state.ticksWaveMode});
                float fill=std::clamp(203.f*ticks/std::max(1.f,(float)maxTicks),0.f,203.f);
                if(fill>0.1f)rect(shape,CCRect(x+14,87,fill,6),3,accent);
                if(customStageFor(state.stageIndex)) {
                    b(CCRect(x+145,105,30,27),"-");
                    b(CCRect(x+182,105,30,27),"+");
                }
            }
            t(customStageFor(state.stageIndex)?"Use +/- to adjust this custom stage.":"Preset stages are read-only.",
                204,47,.59f,muted);
        } else if(m_activeTab==2) {
            t("Fine-tune the prediction engine without interrupting gameplay.",204,383,.65f,secondary);
            rect(shape,CCRect(203,297,471,66),12,card,10);
            t("Input correction",218,339,.78f,white,true);
            t("Master timing adjustment",218,315,.60f,muted);
            b(CCRect(609,318,42,26),mod->getSettingValue<bool>("input-enabled")?"ON":"OFF",
                mod->getSettingValue<bool>("input-enabled"),.64f);
            rect(shape,CCRect(203,225,471,65),12,card,10);
            t("Correction strength",218,264,.77f,white,true);
            double strength=mod->getSettingValue<double>("input-strength");
            t(fmt::format("{:.2f}x",strength),218,241,.68f,accent,true);
            rect(shape,CCRect(405,246,171,5),2.5f,hexColor(0x3C404E));
            rect(shape,CCRect(405,246,std::max(2.f,(float)((strength-.5)*171.)),5),
                2.5f,accent);
            rect(shape,CCRect(405.f+(float)((strength-.5)*171.)-5.f,241,10,15),5,white);
            b(CCRect(591,237,30,28),"-");b(CCRect(631,237,30,28),"+");
            section("INPUT ACTIONS",210);
            b(CCRect(481,179,83,30),
                mod->getSettingValue<bool>("input-presses")?"Press ON":"Press OFF",
                mod->getSettingValue<bool>("input-presses"),.58f);
            b(CCRect(574,179,89,30),
                mod->getSettingValue<bool>("input-releases")?"Release ON":"Release OFF",
                mod->getSettingValue<bool>("input-releases"),.58f);
            section("ENABLED GAMEMODES",157);
            static char const* modes[]={"Cube","Ship","Ball","UFO","Wave","Robot","Spider","Swing"};
            for(int i=0;i<8;++i) {
                CCRect rr(208.f+i%4*114.f,90.f-i/4*40.f,105.f,31.f);
                bool isOn=mod->getSettingValue<bool>(fmt::format("input-{}",AURORA_MODES[i]));
                b(rr,modes[i],isOn,.66f);
                shape->drawCircle(CCPoint(rr.getMinX()+10,rr.getMidY()),
                    2.7f,color4(isOn?accent:muted),0.f,color4(0,0,0,0),12);
            }
            t("Changes apply to the active engine and are saved by Geode.",204,42,.55f,muted);
        } else if(m_activeTab==3) {
            t("Local diagnostics from the live correction queue.",204,383,.67f,secondary);
            for(int i=0;i<3;++i) {
                float x=203.f+i*160.f;
                rect(shape,CCRect(x,281,151,76),12,card,9);
                t(i==0?"PRESSES":i==1?"RELEASES":"QUEUED",x+14,334,.55f,muted,true);
                uint64_t value=i==0?g_aurora.pressCount:
                    i==1?g_aurora.releaseCount:g_aurora.queuedCount;
                t(fmt::format("{}",value),x+14,306,.97f,i==2?accent:white,true);
            }
            rect(shape,CCRect(203,127,471,140),12,card,9);
            section("CORRECTION DELAY TIMELINE",245);
            int n=std::min((int)g_aurora.history.size(),30);
            for(int i=0;i<n;++i) {
                auto const& e=g_aurora.history[g_aurora.history.size()-n+i];
                float h=std::clamp((float)e.ticks/32.f*76.f,3.f,76.f);
                float x=224.f+i*14.3f;
                shape->drawSegment(CCPoint(x,148),CCPoint(x,148+h),3.3f,
                    color4(e.press?accent:hexColor(0x83C7CD),205));
            }
            t("Chart tracks queued delays, not verified safe frames.",221,140,.53f,muted);
            b(CCRect(400,73,126,32),"Clear data");
            b(CCRect(538,73,126,32),"Copy CSV");
            t("Up to 80 recent corrections are retained in memory.",205,48,.56f,muted);
        } else if(m_activeTab==4) {
            t("Quick actions for the live engine and level profiles.",204,383,.66f,secondary);
            static char const* actions[]={
                "Toggle correction","Emergency bypass","Adaptive timing","Mini HUD",
                "Copy session CSV","Clear statistics","Save level profile","Load level profile"
            };
            static char const* hints[]={
                "Engine master switch","F8 safety shortcut","Dynamic timing window","Small in-game counter",
                "Copy recorded timing","Reset session data","Bind to current level","Restore level settings"
            };
            for(int i=0;i<8;++i) {
                float x=203.f+i%2*239.f,y=260.f-i/2*60.f;
                rect(shape,CCRect(x,y,226,48),11,card,9);
                t(actions[i],x+13,y+29,.69f,white,true,197);
                t(hints[i],x+13,y+12,.52f,muted,false,197);
            }
        } else if(m_activeTab==5) {
            t("Recall timing setups. Profiles are stored on this device.",204,383,.64f,secondary);
            for(int i=0;i<3;++i) {
                float y=281.f-i*88.f;
                rect(shape,CCRect(203,y-15,471,74),12,card,10);
                t(fmt::format("PROFILE 0{}",i+1),218,y+31,.56f,muted,true);
                t(fmt::format("Local slot {}",i+1),218,y+8,.79f,white,true);
                b(CCRect(520,y,68,32),"Save");
                b(CCRect(596,y,68,32),"Load");
            }
            section("QUICK START",83);
            b(CCRect(210,32,143,34),"Conservative");
            b(CCRect(363,32,143,34),"Balanced",true);
            b(CCRect(516,32,143,34),"Aggressive");
        } else if(m_activeTab==6) {
            t("Expressive details, without visual noise.",204,383,.66f,secondary);
            section("ACCENT PALETTE",346);
            static char const* accents[]={"Iris","Azure","Sage","Amber","Rose","Graphite"};
            for(int i=0;i<6;++i) {
                CCRect box(205.f+i%3*154.f,220.f-i/3*57.f,145.f,46.f);
                rect(shape,box,10,i==palette?active:card,i==palette?26:8);
                shape->drawCircle(CCPoint(box.getMinX()+20,box.getMidY()),6.5f,
                    color4(hexColor(paletteHex[i])),0.f,color4(0,0,0,0),16);
                t(accents[i],box.getMinX()+37,box.getMidY(),.68f,
                    i==palette?white:secondary,true,94);
            }
            section("ANIMATION",139);
            rect(shape,CCRect(203,90,471,43),10,card,9);
            t("Reduced motion",218,110,.72f,white,true);
            b(CCRect(542,93,120,37),
                mod->getSettingValue<bool>("aurora-reduce-motion")?"Enabled":"Disabled",
                mod->getSettingValue<bool>("aurora-reduce-motion"));
            section("WINDOW SCALE",78);
            double scale=mod->getSettingValue<double>("ui-panel-scale");
            t(fmt::format("{:.0f}%",scale*100.),482,57,.69f,accent,true,68);
            b(CCRect(567,44,43,28),"-");b(CCRect(617,44,43,28),"+");
            t("Afterflow by sevend and contributors",203,23,.53f,muted);
        }
        if(previousTab>=0 && previousTab!=m_activeTab &&
           !mod->getSettingValue<bool>("aurora-reduce-motion")) {
            m_v4Page->setOpacity(0);
            m_v4Page->setPosition(CCPoint(8.f,0.f));
            m_v4Page->runAction(CCFadeTo::create(.16f*uiMotion(),255));
            m_v4Page->runAction(CCEaseSineOut::create(
                CCMoveTo::create(.22f*uiMotion(),CCPoint(0,0))));
        }
    }

'''
