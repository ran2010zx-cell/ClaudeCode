// Flomo API 工具函数

/**
 * 保存内容到 flomo
 * @param {string} content - 要保存的内容
 * @param {string} apiToken - flomo API token
 * @returns {Promise<{success: boolean, error?: string}>}
 */
async function saveToFlomo(content, apiToken) {
  try {
    const response = await fetch('https://flomoapp.com/iwh/' + apiToken, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        content: content
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();

    if (data.code === 0) {
      return { success: true };
    } else {
      return { success: false, error: data.message || '未知错误' };
    }
  } catch (error) {
    console.error('保存到 flomo 失败:', error);
    return { success: false, error: error.message };
  }
}

/**
 * 测试 flomo API 连接
 * @param {string} apiToken - flomo API token
 * @returns {Promise<{success: boolean, error?: string}>}
 */
async function testFlomoConnection(apiToken) {
  return await saveToFlomo('🧪 测试连接成功！\n\n这是来自 Flomo 智能助手的测试消息。', apiToken);
}

/**
 * 获取用户的所有标签
 * @param {string} apiToken - flomo API token
 * @returns {Promise<string[]>}
 */
async function fetchUserTags(apiToken) {
  try {
    // flomo 目前没有公开的 API 来获取标签列表
    // 我们需要从存储中获取历史使用的标签
    const stored = await chrome.storage.local.get(['cachedTags']);
    return stored.cachedTags || [];
  } catch (error) {
    console.error('获取标签失败:', error);
    return [];
  }
}

/**
 * 缓存标签到本地存储
 * @param {string[]} tags - 标签列表
 */
async function cacheTags(tags) {
  try {
    const stored = await chrome.storage.local.get(['cachedTags']);
    const existingTags = stored.cachedTags || [];

    // 合并新标签，去重
    const allTags = [...new Set([...existingTags, ...tags])];

    await chrome.storage.local.set({ cachedTags: allTags });
  } catch (error) {
    console.error('缓存标签失败:', error);
  }
}
