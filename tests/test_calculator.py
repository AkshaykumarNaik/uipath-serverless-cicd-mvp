import pytest

from src.main import CalculatorInput, Operator, apply_operator, main


def test_apply_operator_adds_numbers():
    assert apply_operator(Operator.ADD, 2, 3).result == 5


def test_apply_operator_divide_by_zero_returns_zero():
    assert apply_operator(Operator.DIVIDE, 10, 0).result == 0


@pytest.mark.asyncio
async def test_main_uses_typed_input():
    result = await main(CalculatorInput(a=4, b=5, operator=Operator.MULTIPLY))
    assert result.result == 20
