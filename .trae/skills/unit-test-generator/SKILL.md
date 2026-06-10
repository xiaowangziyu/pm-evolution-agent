---
name: "unit-test-generator"
description: "Generates comprehensive unit tests for code. Invoke when user asks to write tests, generate test cases, or add test coverage."
---

# Unit Test Generator

This skill automatically generates comprehensive unit tests for your code.

## When to Use

Invoke this skill when:
- User asks to write tests for code
- User wants to add test coverage
- User needs test cases for a function/module
- User asks to generate unit tests
- User wants to improve test coverage

## Test Generation Strategy

### 1. Code Analysis
- Identify functions, classes, and modules
- Analyze function signatures and dependencies
- Determine test scenarios

### 2. Test Case Design

#### Positive Tests
- Test with valid inputs
- Verify expected outputs
- Check normal behavior

#### Negative Tests
- Test with invalid inputs
- Verify error handling
- Check edge cases

#### Boundary Tests
- Test with boundary values
- Check minimum/maximum inputs
- Verify limits

### 3. Test Coverage

#### Statement Coverage
- Ensure each line is executed
- Basic coverage requirement

#### Branch Coverage
- Test both true and false branches
- Improve decision point coverage

#### Path Coverage
- Test all possible execution paths
- Comprehensive coverage

## Usage Example

```python
# Example: Generate tests for a calculator function
def add(a, b):
    """Add two numbers"""
    return a + b

# Generated tests:
def test_add_positive_numbers():
    assert add(2, 3) == 5

def test_add_negative_numbers():
    assert add(-1, -1) == -2

def test_add_mixed_numbers():
    assert add(5, -3) == 2

def test_add_zero():
    assert add(0, 5) == 5
    assert add(5, 0) == 5
```

## Best Practices

1. **Arrange-Act-Assert**: Structure tests clearly
2. **One Assertion Per Test**: Keep tests focused
3. **Descriptive Names**: Use clear test names
4. **Test Independence**: Avoid test dependencies
5. **Regular Updates**: Update tests when code changes

## Framework Support

This skill generates tests for:
- **Python**: pytest, unittest, doctest
- **JavaScript**: Jest, Mocha, Vitest
- **TypeScript**: Jest, Vitest
- **Other**: Adaptable to most testing frameworks

## Test Generation Workflow

1. **Read Code**: Analyze the target code
2. **Identify Scenarios**: Determine test cases needed
3. **Generate Tests**: Create test functions
4. **Review Quality**: Verify test completeness
5. **Suggest Improvements**: Recommend coverage enhancements