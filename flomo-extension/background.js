// 导入 API 工具
importScripts('utils/api.js', 'utils/tagSuggestion.js');

// 创建右键菜单
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'saveToFlomo',
    title: '保存到 flomo',
    contexts: ['selection']
  });
});

// 通用的保存选中文本到 flomo 的函数
async function saveSelectionToFlomo(selectedText, pageUrl, pageTitle) {
  try {
    if (!selectedText) {
      showNotification('未选中任何文本', 'error');
      return { success: false, error: '未选中任何文本' };
    }

    // 显示加载中的通知
    showNotification('正在保存到 flomo...', 'loading');

    // 获取用户设置
    const settings = await chrome.storage.sync.get(['apiToken', 'autoTag', 'includeSource']);

    if (!settings.apiToken) {
      showNotification('请先配置 flomo API Token', 'error');
      chrome.runtime.openOptionsPage();
      return { success: false, error: '未配置 API Token' };
    }

    // 获取智能标签推荐
    let tags = [];
    if (settings.autoTag !== false) {
      tags = await suggestTags(selectedText, settings.apiToken);
    }

    // 构建 memo 内容
    let content = selectedText;

    // 添加来源（如果启用）
    if (settings.includeSource !== false) {
      content += `\n\n---\n来源: [${pageTitle}](${pageUrl})`;
    }

    // 添加标签
    if (tags.length > 0) {
      content += '\n\n' + tags.map(tag => `#${tag}`).join(' ');
    }

    // 保存到 flomo
    const result = await saveToFlomo(content, settings.apiToken);

    if (result.success) {
      showNotification('✓ 已保存到 flomo' + (tags.length > 0 ? ` (标签: ${tags.join(', ')})` : ''), 'success');
      return { success: true, tags };
    } else {
      showNotification('保存失败: ' + result.error, 'error');
      return result;
    }

  } catch (error) {
    console.error('保存到 flomo 失败:', error);
    showNotification('保存失败: ' + error.message, 'error');
    return { success: false, error: error.message };
  }
}

// 处理右键菜单点击
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === 'saveToFlomo') {
    await saveSelectionToFlomo(info.selectionText, tab.url, tab.title);
  }
});

// 监听快捷键命令
chrome.commands.onCommand.addListener(async (command) => {
  if (command === 'save-to-flomo') {
    try {
      // 获取当前活动标签页
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

      if (!tab) {
        showNotification('无法获取当前页面', 'error');
        return;
      }

      // 从 content script 获取选中的文本
      const response = await chrome.tabs.sendMessage(tab.id, { action: 'getSelection' });

      if (response && response.selectedText) {
        await saveSelectionToFlomo(response.selectedText, response.pageUrl, response.pageTitle);
      } else {
        showNotification('未选中任何文本', 'error');
      }
    } catch (error) {
      console.error('快捷键保存失败:', error);

      // 检查是否是连接错误
      if (error.message.includes('Could not establish connection') ||
          error.message.includes('Receiving end does not exist')) {
        showNotification('请刷新页面后重试（按 F5）', 'error');
      } else {
        showNotification('保存失败: ' + error.message, 'error');
      }
    }
  }
});

// 显示通知
function showNotification(message, type = 'info') {
  const notificationOptions = {
    type: 'basic',
    iconUrl: 'icons/icon128.png',
    title: 'Flomo 智能助手',
    message: message
  };

  chrome.notifications.create('', notificationOptions);
}

// 监听来自 popup 的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'testConnection') {
    testFlomoConnection(request.apiToken)
      .then(result => sendResponse(result))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true; // 保持消息通道开启
  }

  if (request.action === 'fetchTags') {
    fetchUserTags(request.apiToken)
      .then(tags => sendResponse({ success: true, tags }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }

  if (request.action === 'saveQuickMemo') {
    saveToFlomo(request.content, request.apiToken)
      .then(result => sendResponse(result))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }

  if (request.action === 'saveSelectedText') {
    // 保存当前选中的文本
    chrome.tabs.query({ active: true, currentWindow: true })
      .then(([tab]) => {
        return chrome.tabs.sendMessage(tab.id, { action: 'getSelection' });
      })
      .then(response => {
        if (response && response.selectedText) {
          return saveSelectionToFlomo(response.selectedText, response.pageUrl, response.pageTitle);
        } else {
          return { success: false, error: '未选中任何文本' };
        }
      })
      .then(result => sendResponse(result))
      .catch(error => {
        // 检查是否是连接错误
        if (error.message.includes('Could not establish connection') ||
            error.message.includes('Receiving end does not exist')) {
          sendResponse({ success: false, error: '请刷新页面后重试（按 F5）' });
        } else {
          sendResponse({ success: false, error: error.message });
        }
      });
    return true;
  }
});
