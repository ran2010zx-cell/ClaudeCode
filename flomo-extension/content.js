// Content Script - 在网页中运行，用于获取选中的文本

// 监听来自 background 或 popup 的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getSelection') {
    // 获取当前选中的文本
    const selectedText = window.getSelection().toString().trim();
    const pageUrl = window.location.href;
    const pageTitle = document.title;

    sendResponse({
      selectedText: selectedText,
      pageUrl: pageUrl,
      pageTitle: pageTitle
    });
  }

  return true; // 保持消息通道开启
});

// 监听快捷键（如果通过 content script）
// 注：主要通过 background.js 的 commands API 处理
