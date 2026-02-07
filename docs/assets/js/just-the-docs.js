// Just the Docs - Fixed Search for GitHub Pages with baseurl
document.addEventListener('DOMContentLoaded', function() {
  var searchInput = document.getElementById('search-input');
  if (!searchInput) return;

  // Dynamically determine baseurl from current page
  var baseurl = '';
  if (window.location.pathname.startsWith('/CoeHarMod')) {
    baseurl = '/CoeHarMod';
  }

  fetch(baseurl + '/assets/js/search-data.json')
    .then(response => response.json())
    .then(data => {
      // Load Lunr.js from CDN
      var script = document.createElement('script');
      script.src = 'https://fastly.jsdelivr.net/npm/lunr@2.3.9/lunr.min.js';
      script.onload = function() {
        var idx = lunr(function () {
          this.ref('url');
          this.field('title', { boost: 2 });
          this.field('content');
          for (var url in data) {
            this.add({
              url: url,
              title: data[url].title,
              content: data[url].content
            });
          }
        });

        var resultsContainer = document.getElementById('search-results');
        if (!resultsContainer) {
          resultsContainer = document.createElement('div');
          resultsContainer.id = 'search-results';
          resultsContainer.style.cssText = `
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 1px solid #ddd;
            max-height: 300px;
            overflow-y: auto;
            z-index: 1000;
          `;
          searchInput.parentNode.appendChild(resultsContainer);
        }

        searchInput.addEventListener('input', function () {
          var query = this.value.trim();
          if (!query) {
            resultsContainer.innerHTML = '';
            return;
          }

          var results = idx.search(query + '*').map(r => {
            var item = data[r.ref];
            return `<a href="${baseurl}${r.ref}" style="display:block;padding:8px 12px;text-decoration:none;color:#000;border-bottom:1px solid #eee;">${item.title}</a>`;
          }).join('');

          resultsContainer.innerHTML = results || '<div style="padding:8px 12px;color:#666;">No results</div>';
        });
      };
      document.head.appendChild(script);
    })
    .catch(err => console.error('Search error:', err));
});