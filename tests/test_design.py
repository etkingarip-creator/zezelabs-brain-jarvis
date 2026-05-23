import pytest

@pytest.mark.anyio
async def test_visual_director():
    from core.ai.providers.visual_director import VisualDirector
    director = VisualDirector()
    result = await director.analyze("premium neon visual style")
    assert isinstance(result, dict)
    assert result["style"] == "premium_neon_glassmorphism"
    assert "colors" in result
    assert result["typography"] == "Segoe UI"
    assert result["conversion_optimization"] == "high"

@pytest.mark.anyio
async def test_parametric_sculptor():
    from core.ai.providers.parametric_sculptor import ParametricSculptor
    sculptor = ParametricSculptor()
    result = await sculptor.sculpt({"ratio": "3:1", "margin": 0.20})
    assert isinstance(result, dict)
    assert result["ratio"] == "3:1"
    assert result["margin"] == 0.20
    assert result["resolution"] == "300dpi"
    assert result["validation"] == "pass"

@pytest.mark.anyio
async def test_layout_composer():
    from core.ai.providers.layout_composer import LayoutComposer
    composer = LayoutComposer()
    result = await composer.compose({})
    assert isinstance(result, dict)
    assert "template" in result
    assert result["injected"] is True
    assert result["n8n_integration"] == "active"

@pytest.mark.anyio
async def test_design_agent_methods():
    from departments.zeze_design.agent import ZezeDesignAgent
    agent = ZezeDesignAgent()
    
    # 1. Test visual generation
    visual_res = await agent.run_visual_generation("corporate portal branding")
    assert visual_res.success is True
    assert visual_res.department == "zeze_design"
    assert len(visual_res.tool_results) == 1
    assert "aesthetic_plan.json" in visual_res.tool_results[0]["files_created"][1]
    
    # 2. Test parametric design
    param_res = await agent.run_parametric_design("kupa wrap", {"ratio": "3:1", "margin": 0.20})
    assert param_res.success is True
    assert "parametric_specs.json" in param_res.tool_results[0]["files_created"][1]

    # 3. Test layout composition
    layout_res = await agent.run_layout_composition("web template layout", {"ratio": "16:9"})
    assert layout_res.success is True
    assert "composed_layout.json" in layout_res.tool_results[0]["files_created"][1]

    # 4. Test n8n integration
    n8n_res = await agent.run_n8n_integration("pipeline sync")
    assert n8n_res.success is True
    assert "n8n_workflow.json" in n8n_res.tool_results[0]["files_created"][1]

@pytest.mark.anyio
async def test_design_agent_cycle():
    from departments.zeze_design.agent import ZezeDesignAgent
    agent = ZezeDesignAgent()
    cycle_res = await agent.run_cycle()
    assert isinstance(cycle_res, dict)
    assert "aesthetic" in cycle_res
    assert "parametric" in cycle_res
    assert "layout" in cycle_res
    assert cycle_res["aesthetic"]["style"] == "premium_neon_glassmorphism"
    assert cycle_res["parametric"]["ratio"] == "3:1"
    assert cycle_res["layout"]["injected"] is True
