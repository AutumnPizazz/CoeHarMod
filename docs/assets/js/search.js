// 按字符切分中文，保留英文单词
function tokenize(text) {
  if (!text) return [];
  // 匹配：中文字符 / 英文单词 / 数字
  const tokens = [];
  let current = '';
  for (let char of text) {
    if (/[\u4e00-\u9fa5]/.test(char)) {
      // 中文字符：单独成词
      if (current) {
        tokens.push(current.toLowerCase());
        current = '';
      }
      tokens.push(char);
    } else if (/[a-zA-Z0-9]/.test(char)) {
      // 英文或数字：拼接
      current += char;
    } else {
      // 其他字符（标点、空格等）：断开
      if (current) {
        tokens.push(current.toLowerCase());
        current = '';
      }
    }
  }
  if (current) tokens.push(current.toLowerCase());
  return tokens;
}

// 初始化 MiniSearch
const miniSearch = new MiniSearch({
  fields: ['title', 'content'],
  storeFields: ['title', 'href'],
  tokenize: tokenize,
  processTerm: (term) => term
});

// 页面加载后初始化搜索
document.addEventListener('DOMContentLoaded', function () {
  const searchData = window.searchData || [];
  miniSearch.addAll(searchData);

  const searchInput = document.getElementById('search-input');
  const resultsContainer = document.getElementById('search-results');

  if (!searchInput || !resultsContainer) return;

  let searchTimeout;
  searchInput.addEventListener('input', function () {
    clearTimeout(searchTimeout);
    const query = this.value.trim();
    
    if (query === '') {
      resultsContainer.innerHTML = '';
      return;
    }

    searchTimeout = setTimeout(() => {
      const results = miniSearch.search(query, { prefix: true, fuzzy: 0.2, boost: { title: 2 } });
      if (results.length === 0) {
        resultsContainer.innerHTML = '<li>未找到结果</li>';
      } else {
        resultsContainer.innerHTML = results.map(r => 
          `<li><a href="${r.href}">${r.title}</a></li>`
        ).join('');
      }
    }, 200);
  });
});