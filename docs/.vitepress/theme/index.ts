import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import Layout from './Layout.vue'
import VideoEmbed from './VideoEmbed.vue'
import LearningMap from './LearningMap.vue'
import { defineAsyncComponent } from 'vue'
import LabStatus from './LabStatus.vue'
import LabOverview from './LabOverview.vue'
import RegisterExplorer from './RegisterExplorer.vue'
import ClockCalc from './ClockCalc.vue'
import BaudCalc from './BaudCalc.vue'
import QuizBank from './QuizBank.vue'
import PathFinder from './PathFinder.vue'
import McuCta from './McuCta.vue'
import McuUpdates from './McuUpdates.vue'
import './custom.css'

export default {
  extends: DefaultTheme,
  Layout,
  enhanceApp({ app }) {
    app.component('VideoEmbed', VideoEmbed)
    app.component('LearningMap', LearningMap)
    app.component('AnimFigure', defineAsyncComponent(() => import('./AnimFigure.vue')))
    app.component('LabStatus', LabStatus)
    app.component('LabOverview', LabOverview)
    app.component('RegisterExplorer', RegisterExplorer)
    app.component('ClockCalc', ClockCalc)
    app.component('BaudCalc', BaudCalc)
    app.component('QuizBank', QuizBank)
    app.component('PathFinder', PathFinder)
    app.component('McuCta', McuCta)
    app.component('McuUpdates', McuUpdates)
  },
} satisfies Theme
