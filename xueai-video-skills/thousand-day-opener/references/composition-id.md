# Remotion Composition ID 说明

本 skill 依赖 Remotion 项目里注册的 `Opener` composition。

## 注册位置

`D:/video/_系统/remotion-base/src/Root.tsx`：

```tsx
<Composition
  id="Opener"
  component={Opener01_SeriesCounter}
  durationInFrames={150}    // 5 秒 @ 30fps
  fps={30}
  width={1920}
  height={1080}
  defaultProps={Opener01SeriesCounterDefaults}
/>
```

## Props 接口

来自 `src/openers/Opener01_SeriesCounter.tsx`：

```ts
type Opener01Props = {
  dayNumber: number;       // 第几天
  totalDays: number;       // 系列总天数
  topic: string;           // 副标题（"今天学：xxx"）
  episodeLabel: string;    // EP 标识（已弃用 · 传空字符串）
  dateLabel: string;       // 日期 "YYYY·MM·DD"
};
```

## 渲染命令对照

### 视频（5 秒 mp4）
```bash
cd D:/video/_系统/remotion-base
npx remotion render Opener \
    --props='{"dayNumber":30,"totalDays":1000,"topic":"今天学：龙虾接微信","episodeLabel":"","dateLabel":"2026·05·06"}' \
    out.mp4
```

### 单帧（PNG）
```bash
cd D:/video/_系统/remotion-base
npx remotion still Opener \
    --props='{"dayNumber":30,...}' \
    --frame=75 \
    out.png
```

`--frame=75`（5 秒视频中点 · 数字 + 标题完全站定）适合做封面。

## 改时长

默认 5 秒（150f）。要改：

- 编辑 `Root.tsx` 里 `durationInFrames={150}` → 改成 `90`（3 秒） / `300`（10 秒）
- 同时检查 `Opener01_SeriesCounter.tsx` 内动画 `interpolate` 终点是否超过新时长

## 改组件视觉

颜色 / 字体 / 布局都在：

- `src/openers/Opener01_SeriesCounter.tsx` — 主组件
- `src/components/Kicker.tsx` / `BrandMark.tsx` / `BottomMeta.tsx` / `Rule.tsx` — 子模块
- `src/theme/colors.ts` — 颜色 token
- `src/theme/typography.ts` — 字体 token
- `src/theme/motion.ts` — 动画 helper（fadeInSoft / snapIn）

## 故障排查

| 问题 | 解 |
|---|---|
| `Composition with id "Opener" not found` | 检查 Root.tsx 是否注册了 Opener composition |
| Props 解析错误 | 检查 JSON 字符串引号转义 · Windows PowerShell 用单引号包 JSON |
| 渲染时找不到 npx | 装 Node.js 22+ 并加 PATH |
