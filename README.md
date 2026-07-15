# Qpet

<p align="center">
  <img src="plugins/qpet/assets/logo.png" width="160" alt="Qpet 奶油卷猫咪头像">
</p>

**输入几个关键词，或者上传一张自拍，就能做出属于自己的 3D Q版桌面宠物。**

Qpet 不要求你懂设计。它会先给你三种明显不同的造型，你选中最喜欢的一种后，再把它做成会动的桌面宠物。

## Qpet 的亮点

- **一句话就能开始**：动物、人物、物品都可以变成 Q版宠物。
- **自拍变成 Q版的自己**：保留你选择的发型、眼镜和服装颜色。
- **先看三种方案再决定**：不是只换颜色，而是三种不同造型。
- **选定后保持一致**：做成动画后，脸、配色和标志性配件不会乱变。
- **不满意可以局部修改**：不用每次全部推倒重来。
- **照片由你主动选择**：Qpet 不会偷偷打开相机，也不会把原始自拍放进宠物文件。

## 发给朋友：最简单的安装方法

把这个地址发给朋友：

https://github.com/liangxin92/qpet

让朋友打开 ChatGPT 桌面版，进入一个新的 Codex 对话，然后发送：

> 请帮我安装 Qpet：https://github.com/liangxin92/qpet 。固定使用 v1.0.1。安装完成后提醒我新建一个 Codex 对话使用。

安装时如果出现确认窗口，点击允许。安装完成后，新建一个 Codex 对话。

## 手动安装

```bash
codex plugin marketplace add liangxin92/qpet --ref v1.0.1
codex plugin add qpet@qpet
```

安装后请新建一个 Codex 对话，让 Qpet 正确加载。

## 怎么使用

### 用关键词制作

> 使用 $qpet:create-chibi-pet，把“薄荷色宇航员柴犬、好奇、软陶质感、小挎包”做成三套不同的 3D Q版宠物方案。

### 用自拍制作

先在对话中主动附加照片，再发送：

> 使用 $qpet:create-chibi-pet，把我的自拍做成三套 3D Q版宠物，保留我的发型、眼镜和蓝色外套。

接下来只需要：

1. 选择 A、B 或 C。
2. 确认制作动画。
3. 确认安装到桌面宠物。

如果提示宠物功能尚未准备好，请先打开一次 **设置 → Pets → Create your own pet**，然后回到新对话重试。

## 目前的边界

Qpet 制作的是看起来像 3D 的动画桌面宠物，不是可以自由旋转的实时 3D 模型。当前桌面宠物也还不能把 ChatGPT 剩余用量显示成 HP 血条。

## English quick start

Qpet turns a few words or an attached selfie into three different 3D chibi looks. Pick your favorite, and Qpet turns it into an animated desktop pet.

```bash
codex plugin marketplace add liangxin92/qpet --ref v1.0.1
codex plugin add qpet@qpet
```

Start a new Codex task after installation.

## 开发者验证

```bash
python3 scripts/verify_marketplace.py
python3 -m unittest discover -s plugins/qpet/tests -v
python3 scripts/package_release.py --output dist
```

See [SUPPORT.md](SUPPORT.md), [SECURITY.md](SECURITY.md), and the [MIT license](LICENSE).
