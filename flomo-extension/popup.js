// Popup 脚本

document.addEventListener('DOMContentLoaded', async () => {
  await loadStatus();
  await loadFrequentTags();

  // 绑定事件
  document.getElementById('saveSelection').addEventListener('click', saveSelectedText);
  document.getElementById('saveMemo').addEventListener('click', saveQuickMemo);
  document.getElementById('openSettings').addEventListener('click', openSettings);
  document.getElementById('openFlomo').addEventListener('click', openFlomo);
});

// 加载状态信息
async function loadStatus() {
  try {
    const settings = await chrome.storage.sync.get(['apiToken', 'autoTag']);

    // 更新连接状态
    const connectionStatus = document.getElementById('connectionStatus');
    if (settings.apiToken) {
      connectionStatus.textContent = '已连接';
      connectionStatus.className = 'status-value connected';
    } else {
      connectionStatus.textContent = '未配置';
      connectionStatus.className = 'status-value disconnected';
    }

    // 更新自动标签状态
    const autoTagStatus = document.getElementById('autoTagStatus');
    autoTagStatus.textContent = settings.autoTag !== false ? '已启用' : '已禁用';

  } catch (error) {
    console.error('加载状态失败:', error);
  }
}

// 加载常用标签
async function loadFrequentTags() {
  try {
    const stored = await chrome.storage.local.get(['tagStats']);
    const tagStats = stored.tagStats || {};

    // 按使用次数排序
    const sortedTags = Object.entries(tagStats)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8)
      .map(([tag]) => tag);

    if (sortedTags.length > 0) {
      const frequentTagsSection = document.getElementById('frequentTagsSection');
      const frequentTagsContainer = document.getElementById('frequentTags');

      frequentTagsContainer.innerHTML = sortedTags
        .map(tag => `<span class="tag" data-tag="${tag}">#${tag}</span>`)
        .join('');

      // 绑定标签点击事件
      frequentTagsContainer.querySelectorAll('.tag').forEach(tagElement => {
        tagElement.addEventListener('click', () => {
          const tag = tagElement.dataset.tag;
          const textarea = document.getElementById('quickMemo');
          textarea.value += ` #${tag}`;
          textarea.focus();
        });
      });

      frequentTagsSection.classList.remove('hidden');
    }

  } catch (error) {
    console.error('加载常用标签失败:', error);
  }
}

// 保存选中的文本
async function saveSelectedText() {
  try {
    // 获取设置
    const settings = await chrome.storage.sync.get(['apiToken']);

    if (!settings.apiToken) {
      alert('请先在设置中配置 API Token');
      openSettings();
      return;
    }

    // 显示保存中状态
    const saveButton = document.getElementById('saveSelection');
    const originalText = saveButton.textContent;
    saveButton.textContent = '⏳ 保存中...';
    saveButton.disabled = true;

    // 发送到后台脚本保存
    const response = await new Promise((resolve) => {
      chrome.runtime.sendMessage({
        action: 'saveSelectedText'
      }, resolve);
    });

    if (response && response.success) {
      // 保存成功
      saveButton.textContent = '✓ 已保存';

      // 2秒后恢复按钮
      setTimeout(() => {
        saveButton.textContent = originalText;
        saveButton.disabled = false;
      }, 2000);

      // 重新加载常用标签
      await loadFrequentTags();

    } else {
      saveButton.textContent = '✗ 保存失败';
      setTimeout(() => {
        saveButton.textContent = originalText;
        saveButton.disabled = false;
      }, 2000);

      const errorMsg = response && response.error ? response.error : '未知错误';
      if (errorMsg === '未选中任何文本') {
        alert('请先在网页中选中要保存的文本！');
      } else {
        alert('保存失败: ' + errorMsg);
      }
    }

  } catch (error) {
    console.error('保存选中文本失败:', error);
    alert('保存失败: ' + error.message);

    const saveButton = document.getElementById('saveSelection');
    saveButton.textContent = '保存当前选中的文本';
    saveButton.disabled = false;
  }
}

// 保存快速备忘
async function saveQuickMemo() {
  try {
    const memoTextarea = document.getElementById('quickMemo');
    const content = memoTextarea.value.trim();

    if (!content) {
      alert('请输入内容');
      return;
    }

    // 获取设置
    const settings = await chrome.storage.sync.get(['apiToken']);

    if (!settings.apiToken) {
      alert('请先在设置中配置 API Token');
      openSettings();
      return;
    }

    // 显示保存中状态
    const saveButton = document.getElementById('saveMemo');
    const originalText = saveButton.textContent;
    saveButton.textContent = '保存中...';
    saveButton.disabled = true;

    // 发送到后台脚本保存
    const response = await new Promise((resolve) => {
      chrome.runtime.sendMessage({
        action: 'saveQuickMemo',
        content: content,
        apiToken: settings.apiToken
      }, resolve);
    });

    if (response && response.success) {
      // 保存成功
      saveButton.textContent = '✓ 已保存';
      memoTextarea.value = '';

      // 2秒后恢复按钮
      setTimeout(() => {
        saveButton.textContent = originalText;
        saveButton.disabled = false;
      }, 2000);

      // 提取并记录标签使用
      const tags = extractTags(content);
      if (tags.length > 0) {
        await recordTagUsage(tags);
        await loadFrequentTags(); // 重新加载常用标签
      }

    } else {
      saveButton.textContent = '✗ 保存失败';
      setTimeout(() => {
        saveButton.textContent = originalText;
        saveButton.disabled = false;
      }, 2000);
      alert('保存失败: ' + (response ? response.error : '未知错误'));
    }

  } catch (error) {
    console.error('保存快速备忘失败:', error);
    alert('保存失败: ' + error.message);
  }
}

// 提取标签
function extractTags(content) {
  const hashTagRegex = /#([\u4e00-\u9fa5a-zA-Z0-9_]+)/g;
  const matches = content.matchAll(hashTagRegex);
  const tags = [];

  for (const match of matches) {
    tags.push(match[1]);
  }

  return tags;
}

// 记录标签使用
async function recordTagUsage(tags) {
  try {
    const stored = await chrome.storage.local.get(['tagStats']);
    const tagStats = stored.tagStats || {};

    for (const tag of tags) {
      tagStats[tag] = (tagStats[tag] || 0) + 1;
    }

    await chrome.storage.local.set({ tagStats });
  } catch (error) {
    console.error('记录标签使用失败:', error);
  }
}

// 打开设置页面
function openSettings() {
  chrome.runtime.openOptionsPage();
}

// 打开 flomo 网页版
function openFlomo() {
  chrome.tabs.create({ url: 'https://flomoapp.com/mine' });
}
