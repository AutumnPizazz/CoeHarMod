// Just the Docs - GitHub Pages Local Search (Minimal)
document.addEventListener('DOMContentLoaded', function() {
  var searchInput = document.querySelector('input#search-input');
  if (!searchInput) return;

  // Load Lunr.js from CDN
  var script = document.createElement('script');
  script.src = 'https://fastly.jsdelivr.net/npm/lunr@2.3.9/lunr.min.js';
  script.onload = function() {
    fetch('/assets/js/search-data.json')
      .then(response => response.json())
      .then(data => {
        // Build index
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

        // Handle input
        searchInput.addEventListener('input', function() {
          var query = this.value.trim();
          var resultsContainer = document.querySelector('#search-results');
          if (!resultsContainer) {
            // Create results container if missing
            resultsContainer = document.createElement('ul');
            resultsContainer.id = 'search-results';
            resultsContainer.style.cssText = 'position:absolute;top:100%;left:0;right:0;background:white;z-index:100;border:1px solid #ddd;padding:0;margin:0;list-style:none;';
            this.parentNode.appendChild(resultsContainer);
          }

          if (query === '') {
            resultsContainer.innerHTML = '';
            return;
          }

          var results = idx.search(query + '*').map(r => {
            var item = data[r.ref];
            return '<li style="padding:8px 12px;border-bottom:1px solid #eee;"><a href="' + r.ref + '">' + item.title + '</a></li>';
          }).join('');

          resultsContainer.innerHTML = results || '<li style="padding:8px 12px;">No results</li>';
        });
      });
  };
  document.head.appendChild(script);
});
