/*!
 * Lunr Languages, `Chinese` module
 * https://github.com/MihaiValentin/lunr-languages
 */
(function(root, factory) {
  if (typeof define === 'function' && define.amd) {
    define(['lunr'], factory);
  } else if (typeof module === 'object' && module.exports) {
    module.exports = factory(require('lunr'));
  } else {
    factory(root.lunr);
  }
})(this, function(lunr) {
  lunr.zh = function(lunr) {
    // 中文按字切分
    lunr.tokenizer.seperator = /[\s\-\.]+/;
    lunr.tokenizer = function(obj) {
      if (!obj || !obj.toString) return [];
      var str = obj.toString().trim();
      if (str === '') return [];
      return str.match(/[\u4e00-\u9fa5]|[\w]+/g) || [];
    };
  };
});