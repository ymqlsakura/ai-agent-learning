# Remotion 四库实测记录

## 来源识别

目标视频为李先森 AI 生活发布的 Remotion 组件库介绍。视频中展示的四个来源经画面、口播、仓库名称和组件数量交叉确认：

1. RVE，对应 `reactvideoeditor/remotion-templates`，81 个模板。
2. Scenes，对应 `lifeprompt-team/remotion-scenes`，仓库说明为 201 个以上场景。
3. Curvable，对应 `Curvable/motion`，14 个组件。
4. Playground，对应 `jessai2026/remotion-playground`，`Root.jsx` 中注册 38 个 Composition，并包含口播提到的波形、频谱和音量控制。

同名的 `remotion-playground` 仓库很多。第四个来源不能只靠仓库名判断，38 个 Composition 和四个音频示例是最终确认依据。

所有上游地址和固定提交记录在 `source-lock.json`。

## 测试环境

- 日期：2026-08-05。
- 系统：Windows。
- Node.js：24.14.0。
- 测试内容：固定提交、安装、许可证、完整类型检查或主入口打包、官方或隔离示例渲染、可见效果复核。
- 测试原则：上游工程失败时保留失败证据，再隔离可用组件测试，不直接修改上游源码冒充通过。

## 测试结果

| 来源 | 固定版本 | 全库检查 | 可见渲染 | 许可证 | 结论 |
| --- | --- | --- | --- | --- | --- |
| RVE | `6209b724798e48ff395f8df1a6fa2d26082372b5` | 81 个模板进入 TypeScript 检查，3 个文件产生 5 个错误。`parallax-pan` 和 `zoom-pulse` 依赖 `next/image`，另有 `style jsx` 类型问题 | 文字高亮、进度步骤和声波可渲染。默认 1920 x 1080 构图过小，需要重做比例 | README 声明 MIT，但固定提交没有 LICENSE 文件 | 参考组件库，不直接作为生产依赖 |
| Scenes | `02c7a84241da7010b5f59c420b0110aafd1d6f0d` | `remotion bundle` 通过，16 个 Showcase 可列出。`eslint src && tsc` 在 `OgpVideo.tsx:181` 因缺少 `palette.primary` 失败 | TextShowcase 成功渲染 | MIT 文件完整 | 大型动作词典，按需参考，不整库进入母版 |
| Curvable | `48aa412b5f4a15d5a31fe02f6e7e43e654ca091a` | 14 个组件完整 TypeScript 检查通过，`npm pack --dry-run` 通过 | Typewriter 和 StatsGrid 成功渲染，14 个官方预览文件齐全 | MIT 文件完整 | 设计质量最佳，可选取少量组件或设计原则进入 XueAI 母版 |
| Playground | `fe10b866da07c5799b226d7ff9598c1dc35d7159` | 主入口在 `BrandShowcase.tsx:186` 因字符串未闭合而无法打包 | 隔离后的 Waveform、Spectrum 和 Volume 可渲染 | LICENSE 为 MIT，`package.json` 却写 ISC | 学习参考，不进入生产依赖 |

## 视觉观察

### RVE

优点是覆盖面广，单文件复制方便。缺点是默认组件更像功能示例，不是完整设计系统。很多模板的字号和画布比例固定，在 1920 x 1080 直接使用会显得空、弱、小。

适合借用：逐词高亮、进度步骤、Ken Burns、图表构造、克制的 Logo 动效。

不适合直接继承：默认皮肤、全库安装、未经改造的画面比例。

### Scenes

优点是动作种类多，能快速回答“这个内容还能怎么动”。缺点是风格跨度大，整库使用会让同一期视频像多个模板网站拼接。官方示例偏单一动效展示，不能替代真实过程镜头。

适合借用：文字遮罩、扰动、形状、背景和局部转场的实现思路。

不适合直接继承：一镜一个 Showcase、混用大量风格、全量依赖。

### Curvable

优点是层级、色场、空间和品牌感最完整。StatsGrid 的卡片组合、倾斜平面、统一主色映射和稳定阅读窗口，是四库中最接近成片设计的方案。

限制是组件少、部分场景是正方形发布素材，且仓库没有发布到 npm。它更适合成为设计母版的参考和经审计的局部组件来源，而不是运行时远程依赖。

### Playground

优点是中文注释和学习示例直观。音频示例使用正弦函数模拟数据，并没有读取真实音频。因此它可以解释波形怎么画，但不能作为“音频驱动动画已经完成”的证据。

默认彩虹频谱和大面积发光更接近教程 Demo，不符合 XueAI 的克制品牌方向。

## 采用决定

核心层：

- XueAI 自有设计母版和系列结构。
- 官方 Remotion API、渲染和转场。
- 真实素材、口播时间点和过程证据。
- Curvable 的色场、空间层级和少量经审计组件。

按镜头可选：

- video-shotcraft 的镜头语言。
- RVE 的单一基础动作。
- Scenes 的单一文字、形状或背景动作。
- 官方音频分析 API 生成的真实波形。

仅参考：

- Playground 全库。
- RVE、Scenes 全库运行时依赖。

拒绝：

- 为了数量把四库一起装进生产母版。
- 用模拟波形冒充真实音频响应。
- 直接复制默认配色和模板排版。
- 上游打包失败时修改源码后声称原库通过。

## 可见测试产物

- 四库原始效果对比：`D:/video/.cache/motion-design/research/li-xiansen-remotion/renders/library-out-of-box-reel.mp4`。
- 推荐设计样片：`D:/video/_worktrees/motion-design-benchmark/out/design-template-videos/template-05-premium-v3.mp4`。
- 推荐样片逐秒接触表：`D:/video/_worktrees/motion-design-benchmark/out/design-template-05-review/every-second-contact.jpg`。
- 口播触发点检查：`D:/video/_worktrees/motion-design-benchmark/out/design-template-05-cues/contact-sheet.jpg`。

这些媒体是本地测试产物，不进入工具仓库 Git 历史。
