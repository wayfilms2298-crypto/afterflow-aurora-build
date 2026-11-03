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
                if(CCRect(x+145.f,88.f,30.f,27.f).containsPoint(p))return 300+i*2;
                if(CCRect(x+182.f,88.f,30.f,27.f).containsPoint(p))return 301+i*2;
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
