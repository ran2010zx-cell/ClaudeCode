// 智能标签推荐功能

/**
 * 基于内容智能推荐标签
 * @param {string} content - 要分析的内容
 * @param {string} apiToken - flomo API token
 * @returns {Promise<string[]>}
 */
async function suggestTags(content, apiToken) {
  try {
    // 获取用户的历史标签
    const stored = await chrome.storage.local.get(['cachedTags', 'tagRules']);
    const cachedTags = stored.cachedTags || [];
    const tagRules = stored.tagRules || getDefaultTagRules();

    const suggestedTags = [];

    // 1. 基于关键词规则匹配
    for (const rule of tagRules) {
      if (matchesRule(content, rule)) {
        suggestedTags.push(rule.tag);
      }
    }

    // 2. 基于内容类型识别
    const contentTypeTags = detectContentType(content);
    suggestedTags.push(...contentTypeTags);

    // 3. 从内容中提取已有的标签格式（#标签）
    const extractedTags = extractHashTags(content);
    suggestedTags.push(...extractedTags);

    // 去重并过滤
    const uniqueTags = [...new Set(suggestedTags)];

    // 限制标签数量（最多3个）
    const finalTags = uniqueTags.slice(0, 3);

    // 更新缓存的标签列表
    if (finalTags.length > 0) {
      await cacheTags(finalTags);
    }

    return finalTags;

  } catch (error) {
    console.error('标签推荐失败:', error);
    return [];
  }
}

/**
 * 检查内容是否匹配规则
 * @param {string} content - 内容
 * @param {Object} rule - 规则对象
 * @returns {boolean}
 */
function matchesRule(content, rule) {
  const lowerContent = content.toLowerCase();

  // 检查是否包含关键词
  if (rule.keywords && Array.isArray(rule.keywords)) {
    return rule.keywords.some(keyword =>
      lowerContent.includes(keyword.toLowerCase())
    );
  }

  // 检查是否匹配正则表达式
  if (rule.pattern) {
    const regex = new RegExp(rule.pattern, 'i');
    return regex.test(content);
  }

  return false;
}

/**
 * 检测内容类型
 * @param {string} content - 内容
 * @returns {string[]}
 */
function detectContentType(content) {
  const tags = [];

  // 检测是否包含代码
  if (content.includes('```') || content.includes('function') || content.includes('const ') || content.includes('import ')) {
    tags.push('代码');
  }

  // 检测是否是引用/摘录
  if (content.includes('>') || content.length > 200) {
    tags.push('摘录');
  }

  // 检测是否包含链接
  if (content.includes('http://') || content.includes('https://')) {
    tags.push('链接');
  }

  // 检测是否包含待办事项
  if (content.includes('TODO') || content.includes('待办') || content.includes('[]')) {
    tags.push('待办');
  }

  return tags;
}

/**
 * 从内容中提取 #标签
 * @param {string} content - 内容
 * @returns {string[]}
 */
function extractHashTags(content) {
  const hashTagRegex = /#([\u4e00-\u9fa5a-zA-Z0-9_]+)/g;
  const matches = content.matchAll(hashTagRegex);
  const tags = [];

  for (const match of matches) {
    tags.push(match[1]);
  }

  return tags;
}

/**
 * 获取默认标签规则
 * @returns {Array}
 */
function getDefaultTagRules() {
  return [
    {
      tag: '学习',
      keywords: ['学习', '教程', '课程', 'learn', 'tutorial', 'course']
    },
    {
      tag: '工作',
      keywords: ['工作', '项目', '会议', 'work', 'project', 'meeting']
    },
    {
      tag: '阅读',
      keywords: ['读书', '阅读', '书籍', 'book', 'reading', 'read']
    },
    {
      tag: '灵感',
      keywords: ['灵感', '想法', '创意', 'idea', 'inspiration', 'creative']
    },
    {
      tag: '技术',
      keywords: ['技术', '编程', '开发', 'tech', 'programming', 'development', 'code']
    },
    {
      tag: '思考',
      keywords: ['思考', '反思', '总结', 'thinking', 'reflection', 'summary']
    },
    {
      tag: '生活',
      keywords: ['生活', '日常', 'life', 'daily']
    },
    {
      tag: '健康',
      keywords: ['健康', '运动', '锻炼', 'health', 'fitness', 'exercise']
    }
  ];
}

/**
 * 更新用户自定义标签规则
 * @param {Array} rules - 规则数组
 */
async function updateTagRules(rules) {
  try {
    await chrome.storage.local.set({ tagRules: rules });
  } catch (error) {
    console.error('更新标签规则失败:', error);
  }
}

/**
 * 获取标签使用统计
 * @returns {Promise<Object>}
 */
async function getTagStats() {
  try {
    const stored = await chrome.storage.local.get(['tagStats']);
    return stored.tagStats || {};
  } catch (error) {
    console.error('获取标签统计失败:', error);
    return {};
  }
}

/**
 * 记录标签使用
 * @param {string[]} tags - 使用的标签
 */
async function recordTagUsage(tags) {
  try {
    const stats = await getTagStats();

    for (const tag of tags) {
      stats[tag] = (stats[tag] || 0) + 1;
    }

    await chrome.storage.local.set({ tagStats: stats });
  } catch (error) {
    console.error('记录标签使用失败:', error);
  }
}
