import { defineConfig } from 'vitepress'
// @ts-ignore
import taskLists from 'markdown-it-task-lists'

export default defineConfig({
  markdown: {
    config: (md) => {
      md.use(taskLists)
    }
  },

  title: 'CoeHarMod',
  description: '和合共生 - Unciv 大型规则集模组',
  base: '/CoeHarMod/',
  lang: 'zh-CN',

  head: [
    ['link', { rel: 'icon', href: '/CoeHarMod/favicon.ico' }],
  ],

  themeConfig: {
    logo: '/logo.webp',

    nav: [
      { text: 'GitHub', link: 'https://github.com/AutumnPizazz/CoeHarMod' },
      { text: '首页', link: '/' },
      { text: '更新日志', link: '/changelog' }
      // {
      //   text: '666', items: [
      //     { text: 'Item A', link: '/item-1' },
      //     { text: 'Item B', link: '/item-2' },
      //     { text: 'Item C', link: '/item-3' }
      //   ]
      // },
    ],

    sidebar: [
      {
        text: '文档',
        items: [
          { text: '首页', link: '/' },
          // {
          //   text: '666', 
          //   collapsed: true,
          //   items: [
          //     { text: 'Item A', link: '/item-1' },
          //     { text: 'Item B', link: '/item-2' },
          //     { text: 'Item C', link: '/item-3' }
          //   ]
          // },
          { 
            text: '更新日志',
            link: '/changelog',
            collapsed: true,
            items: [
              {text: '更新计划', link: '/changeplan'},
            ]
          }
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/AutumnPizazz/CoeHarMod' }
    ],

    search: {
      provider: 'local',
      options: {
        translations: {
          button: {
            buttonText: '搜索文档',
            buttonAriaLabel: '搜索文档'
          },
          modal: {
            noResultsText: '无法找到相关结果',
            resetButtonTitle: '清除查询条件',
            footer: {
              selectText: '选择',
              navigateText: '切换',
              closeText: '关闭'
            }
          }
        }
      }
    },

    outline: {
      label: '页面导航'
    },

    docFooter: {
      prev: '上一页',
      next: '下一页'
    },

    darkModeSwitchLabel: '主题',
    sidebarMenuLabel: '菜单',
    returnToTopLabel: '回到顶部'
  }
})
