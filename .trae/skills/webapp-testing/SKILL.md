---
name: "webapp-testing"
description: "Automates web application testing using Playwright. Invoke when user asks to test web apps, run E2E tests, or perform regression testing."
---

# Web Application Testing

This skill provides comprehensive web application testing capabilities using Playwright.

## When to Use

Invoke this skill when:
- User asks to test a web application
- User needs automated browser testing
- User wants to perform regression testing
- User needs E2E (End-to-End) testing
- User asks to verify web app functionality

## Testing Capabilities

### 1. Browser Automation
- Launch Chromium, Firefox, or WebKit browsers
- Navigate to URLs
- Interact with web elements (click, type, select)
- Take screenshots
- Capture console logs

### 2. Testing Strategies

#### Regression Testing
- Test critical user flows
- Verify existing functionality works after changes
- Run tests in CI/CD pipelines

#### E2E Testing
- Simulate real user interactions
- Test complete user journeys
- Validate multi-step workflows

#### Smoke Testing
- Quick verification of key features
- Run before deployment
- Catch critical issues early

## Usage Example

```javascript
// Example: Test login flow
async function testLogin() {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  await page.goto('https://example.com/login');
  await page.fill('#username', 'testuser');
  await page.fill('#password', 'password123');
  await page.click('#login-button');
  
  // Verify success
  const welcome = await page.textContent('.welcome-message');
  console.log('Login successful:', welcome);
  
  await browser.close();
}
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Clear Assertions**: Make test expectations explicit
3. **Page Objects**: Use Page Object Model for maintainability
4. **Selective Testing**: Don't test everything, test what matters
5. **Regular Updates**: Keep tests in sync with application changes

## Integration

This skill works with:
- Playwright (Python/JavaScript)
- pytest-playwright
- Jest + Playwright
- CI/CD pipelines (GitHub Actions, Jenkins, etc.)