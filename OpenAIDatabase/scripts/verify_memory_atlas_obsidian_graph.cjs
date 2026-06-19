#!/usr/bin/env node
"use strict";

const { chromium } = require("playwright");

const url = process.argv[2] || "http://127.0.0.1:4173";
const chromePath = process.env.PLAYWRIGHT_CHROME || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

function assertCondition(condition, message, detail = {}) {
  if (!condition) {
    const error = new Error(message);
    error.detail = detail;
    throw error;
  }
}

async function main() {
  const browser = await chromium.launch({ headless: true, executablePath: chromePath });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 920 } });
    page.setDefaultTimeout(10000);
    console.error("[obsidian-smoke] open");
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 15000 });
    await page.waitForLoadState("networkidle", { timeout: 8000 }).catch(() => undefined);
    console.error("[obsidian-smoke] switch obsidian");
    await page.getByRole("button", { name: /Obsidian 图谱/ }).click();
    await page.waitForSelector(".obsidian-graph-canvas", { state: "visible" });
    await page.waitForFunction(() => {
      return document.querySelectorAll(".obsidian-node").length > 12 && document.querySelectorAll(".obsidian-link").length > 8;
    }, null, { timeout: 6500 });

    console.error("[obsidian-smoke] inspect initial");
    const initial = await page.evaluate(() => {
      const canvas = document.querySelector(".obsidian-graph-canvas");
      const firstNode = document.querySelector(".obsidian-node");
      return {
        canvas: Boolean(canvas),
        canvasBox: canvas ? canvas.getBoundingClientRect().toJSON() : null,
        nodeCount: document.querySelectorAll(".obsidian-node").length,
        edgeCount: document.querySelectorAll(".obsidian-link").length,
        labelCount: document.querySelectorAll(".obsidian-node-label").length,
        collapsedSettings: Boolean(document.querySelector(".obsidian-settings-collapsed")),
        focusText: document.querySelector(".obsidian-focus-connectivity")?.textContent || "",
        memoryNodeLabels: Array.from(document.querySelectorAll(".obsidian-node"))
          .map((node) => node.getAttribute("aria-label") || "")
          .filter((label) => label.startsWith("记忆 ·"))
          .slice(0, 5),
        firstTransform: firstNode?.getAttribute("transform") || "",
      };
    });

    assertCondition(initial.canvas, "Obsidian graph canvas is missing", initial);
    assertCondition(initial.nodeCount > 12, "Obsidian graph rendered too few nodes", initial);
    assertCondition(initial.edgeCount > 8, "Obsidian graph rendered too few links", initial);
    assertCondition(initial.collapsedSettings, "Obsidian settings collapsed affordance is missing", initial);
    assertCondition(
      initial.focusText.includes("Focus - Connectivity") && initial.focusText.includes("连接") && initial.focusText.includes("关系密度"),
      "Obsidian Focus - Connectivity strip is missing core metrics",
      initial,
    );
    assertCondition(
      initial.memoryNodeLabels.some((label) => (label.match(/ · /g) || []).length >= 3),
      "Obsidian memory node labels do not follow level-theme-keyword shape",
      initial,
    );

    console.error("[obsidian-smoke] open settings");
    await page.getByRole("button", { name: /打开或收起图谱设置/ }).click();
    await page.waitForSelector(".obsidian-settings-panel", { state: "visible" });
    const panelText = await page.locator(".obsidian-settings-panel").innerText();
    assertCondition(
      ["过滤器", "分组", "显示", "力", "搜索文件", "文字淡出阈值", "中心力", "排斥力"].every((label) => panelText.includes(label)),
      "Obsidian settings panel is missing core Graph View sections",
      { panelText },
    );
    await page.locator(".obsidian-settings-head button", { hasText: "收起" }).click();
    await page.waitForSelector(".obsidian-settings-collapsed", { state: "visible" });

    console.error("[obsidian-smoke] hover");
    const firstNode = page.locator(".obsidian-node").first();
    const nodeBox = await firstNode.boundingBox();
    assertCondition(Boolean(nodeBox), "First Obsidian node has no bounding box", initial);
    await page.mouse.move(nodeBox.x + nodeBox.width / 2, nodeBox.y + nodeBox.height / 2);
    await page.waitForTimeout(250);
    const hover = await page.evaluate(() => ({
      focusedLinks: document.querySelectorAll(".obsidian-link.focused").length,
      dimmedNodes: document.querySelectorAll(".obsidian-node.dimmed").length,
    }));
    assertCondition(hover.focusedLinks > 0 || hover.dimmedNodes > 0, "Hover did not expose neighborhood focus state", hover);

    console.error("[obsidian-smoke] zoom");
    const canvasBox = await page.locator(".obsidian-graph-canvas").boundingBox();
    assertCondition(Boolean(canvasBox), "Obsidian canvas has no bounding box", initial);
    await page.evaluate(() => {
      const canvas = document.querySelector(".obsidian-graph-canvas");
      const rect = canvas?.getBoundingClientRect();
      if (!canvas || !rect) return;
      canvas.dispatchEvent(new WheelEvent("wheel", {
        bubbles: true,
        cancelable: true,
        clientX: rect.left + rect.width / 2,
        clientY: rect.top + rect.height / 2,
        deltaY: -620,
      }));
    });
    await page.waitForTimeout(180);
    const zoomed = await page.evaluate(() => {
      const graphLayer = document.querySelector(".obsidian-graph-canvas g[transform]");
      return graphLayer?.getAttribute("transform") || "";
    });
    assertCondition(/scale\((?!1(?:\.0+)?\))/.test(zoomed), "Wheel zoom did not change graph transform", { zoomed });

    const beforeDrag = await firstNode.evaluate((node) => node.getAttribute("transform") || "");
    console.error("[obsidian-smoke] drag");
    await page.mouse.move(nodeBox.x + nodeBox.width / 2, nodeBox.y + nodeBox.height / 2);
    await page.mouse.down();
    await page.mouse.move(nodeBox.x + nodeBox.width / 2 + 80, nodeBox.y + nodeBox.height / 2 + 52, { steps: 10 });
    await page.mouse.up();
    await page.waitForTimeout(260);
    const afterDrag = await firstNode.evaluate((node) => node.getAttribute("transform") || "");
    assertCondition(beforeDrag !== afterDrag, "Node drag did not update node position", { beforeDrag, afterDrag });

    console.error("[obsidian-smoke] summary");
    await page.locator('button[title="总结与迭代"]').click({ force: true, timeout: 5000 });
    await page.waitForSelector(".summary-iteration-view", { state: "visible" });
    const summaryText = await page.locator(".summary-iteration-view").innerText();
    assertCondition(
      ["更新时间", "Personalization", "Agents.md", "config.toml", "Memory"].every((label) => summaryText.includes(label)),
      "Summary & Iteration view is missing agent personalization/config sections",
      { summaryText: summaryText.slice(0, 1000) },
    );

    await page.screenshot({ path: "/private/tmp/memory-atlas-obsidian-smoke.png", fullPage: false });
    console.log(JSON.stringify({ status: "PASS", initial, hover, zoomed, beforeDrag, afterDrag }, null, 2));
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(JSON.stringify({ status: "FAIL", message: error.message, detail: error.detail || null }, null, 2));
  process.exit(1);
});
