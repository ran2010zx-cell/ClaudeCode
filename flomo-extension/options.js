// 选项页面脚本

// 加载设置
document.addEventListener('DOMContentLoaded', async () => {
  loadSettings();

  // 绑定事件
  document.getElementById('saveSettings').addEventListener('click', saveSettings);
  document.getElementById('resetSettings').addEventListener('click', resetSettings);
  document.getElementById('testConnection').addEventListener('click', testConnection);
});

// 加载已保存的设置
async function loadSettings() {
  try {
    const settings = await chrome.storage.sync.get([
      'apiToken',
      'autoTag',
      'includeSource'
    ]);

    document.getElementById('apiToken').value = settings.apiToken || '';
    document.getElementById('autoTag').checked = settings.autoTag !== false;
    document.getElementById('includeSource').checked = settings.includeSource !== false;

  } catch (error) {
    console.error('加载设置失败:', error);
    showStatus('saveStatus', '加载设置失败: ' + error.message, 'error');
  }
}

// 保存设置
async function saveSettings() {
  try {
    const apiToken = document.getElementById('apiToken').value.trim();
    const autoTag = document.getElementById('autoTag').checked;
    const includeSource = document.getElementById('includeSource').checked;

    if (!apiToken) {
      showStatus('saveStatus', '请输入 API Token', 'error');
      return;
    }

    await chrome.storage.sync.set({
      apiToken,
      autoTag,
      includeSource
    });

    showStatus('saveStatus', '✓ 设置已保存', 'success');

  } catch (error) {
    console.error('保存设置失败:', error);
    showStatus('saveStatus', '保存失败: ' + error.message, 'error');
  }
}

// 重置设置
async function resetSettings() {
  if (!confirm('确定要重置所有设置吗？')) {
    return;
  }

  try {
    await chrome.storage.sync.clear();
    await chrome.storage.local.clear();

    document.getElementById('apiToken').value = '';
    document.getElementById('autoTag').checked = true;
    document.getElementById('includeSource').checked = true;

    showStatus('saveStatus', '✓ 设置已重置', 'success');

  } catch (error) {
    console.error('重置设置失败:', error);
    showStatus('saveStatus', '重置失败: ' + error.message, 'error');
  }
}

// 测试连接
async function testConnection() {
  try {
    const apiToken = document.getElementById('apiToken').value.trim();

    if (!apiToken) {
      showStatus('connectionStatus', '请先输入 API Token', 'error');
      return;
    }

    showStatus('connectionStatus', '正在测试连接...', 'success');

    // 发送测试消息到后台脚本
    const response = await chrome.runtime.sendMessage({
      action: 'testConnection',
      apiToken: apiToken
    });

    if (response.success) {
      showStatus('connectionStatus', '✓ 连接成功！已向你的 flomo 发送测试消息', 'success');
    } else {
      showStatus('connectionStatus', '✗ 连接失败: ' + (response.error || '未知错误'), 'error');
    }

  } catch (error) {
    console.error('测试连接失败:', error);
    showStatus('connectionStatus', '✗ 测试失败: ' + error.message, 'error');
  }
}

// 显示状态消息
function showStatus(elementId, message, type) {
  const statusElement = document.getElementById(elementId);
  statusElement.textContent = message;
  statusElement.className = `status-message ${type} show`;

  // 3秒后自动隐藏
  setTimeout(() => {
    statusElement.classList.remove('show');
  }, 3000);
}
