# 公众号排版助手桌面发行

在 Releases 下载桌面安装包。此仓库包含发行文件和桌面更新策略。

维护者可在 Actions 中运行 `Publish desktop update policy`，填写已发布的最新版本和最低支持版本。低于最低版本的客户端会提示必须更新后才能复制到公众号。生成策略前会检查 Windows、Apple 芯片 Mac 和 Intel Mac 安装包。更新策略由仓库密钥签名，有效期一年，需要在到期前重新运行该任务。
