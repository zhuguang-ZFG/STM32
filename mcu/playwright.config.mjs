import { defineConfig } from '@playwright/test'
export default defineConfig({
  testDir: './tests/browser',
  // 仅 CI 允许重试一次：吸收 runner 负载抖动；本地保持 0 次，让真失败立刻暴露。
  retries: process.env.CI ? 1 : 0,
  use: {
    baseURL: 'http://127.0.0.1:24318/mcu/',
    channel: process.env.PLAYWRIGHT_CHANNEL || undefined,
    viewport: { width: 1280, height: 900 },
    trace: 'retain-on-failure',
  },
  webServer: {
    command: 'npm run docs:preview -- --host 127.0.0.1 --port 24318',
    // 端口必须避开 Linux ephemeral 范围（32768-60999）：43188 在 CI 上
    // 偶发被其他进程当临时端口抢用，preview bind 就 EADDRINUSE。
    url: 'http://127.0.0.1:24318/mcu/',
    reuseExistingServer: false,
    timeout: 30000,
  },
})
