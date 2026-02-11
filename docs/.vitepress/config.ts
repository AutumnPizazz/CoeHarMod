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
      {
        text: '原版专区',
        link: '/原版专区/军事实力计算方式'
      },
      {
        text: 'CoeHarMod专区',
        items: [
          { text: '更新记录', link: '/CoeHarMod专区/更新日志' },
          { text: '更新计划', link: '/CoeHarMod专区/更新计划' }
        ]
      }
    ],

    sidebar: [
      {
        text: '文档',
        items: [
          { text: '首页', link: '/' }
        ]
      },
      {
        text: '原版专区',
        collapsed: true,
        items: [
          { text: '军事实力计算', link: '/原版专区/军事实力计算方式' }
        ]
      },
      {
        text: 'CoeHarMod专区',
        collapsed: true,
        items: [
          { text: '更新记录', link: '/CoeHarMod专区/更新日志' },
          { text: '更新计划', link: '/CoeHarMod专区/更新计划' }
        ]
      },
      {
        text: '其他模组专区',
        collapsed: true,
        items: []
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
