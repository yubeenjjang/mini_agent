from app.agents.models import AgentProfile

RECOMMEND_AGENT = AgentProfile(
    agent_id="recommend",
    name="상품 추천 Agent",
    goal="사용자의 예산에 맞는 구매 가능한 상품을 추천합니다.",
    description="예산과 구매 조건을 바탕으로 적합한 상품을 안내합니다.",
    example_question="4만 원 이하로 살 수 있는 상품 추천해줘",
    instructions=(
        "사용자의 예산을 파악한 뒤 recommend_product_by_budget Tool을 호출하세요. "
        "재고가 있는 상품만 추천하고, 추천 이유와 가격을 함께 안내하세요."
    ),
    allowed_tools=frozenset({"recommend_product_by_budget"}),
)