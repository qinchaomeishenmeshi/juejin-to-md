import requests
from bs4 import BeautifulSoup, NavigableString, Tag

# GUI imports
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
except ImportError:
    tk = None


def fetch_article_html(url, headers):
    """
    抓取页面并返回 <article> 标签的 HTML 内容；过滤掉 <style> 标签
    """
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    article = soup.find('article', class_='article')
    if not article:
        messagebox.showerror("错误", "未找到 <article class='article'> 元素，请检查页面源码或请求头。")
        return None

    # 移除所有 <style> 标签
    for style in article.find_all('style'):
        style.decompose()

    return article


def html_to_markdown(element):
    """
    递归将 BeautifulSoup 元素转换为 Markdown 文本。
    支持 h1-h6, p, strong, em, a, ul, ol, li, blockquote, img。
    """
    md_lines = []

    def recurse(node, prefix=""):
        if isinstance(node, NavigableString):
            text = node.strip()
            if text:
                md_lines.append(prefix + text)
            return
        if not isinstance(node, Tag):
            return
        if node.name == 'style':
            return
        if node.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            level = int(node.name[1])
            md_lines.append('#' * level + ' ' + node.get_text(strip=True))
            md_lines.append('')
            return
        if node.name == 'p':
            text = node.get_text(strip=True)
            if text:
                md_lines.append(text)
                md_lines.append('')
            return
        if node.name == 'ul':
            for li in node.find_all('li', recursive=False):
                md_lines.append(prefix + '- ' + li.get_text(strip=True))
            md_lines.append('')
            return
        if node.name == 'ol':
            for i, li in enumerate(node.find_all('li', recursive=False), start=1):
                md_lines.append(prefix + f'{i}. ' + li.get_text(strip=True))
            md_lines.append('')
            return
        if node.name == 'blockquote':
            for child in node.children:
                recurse(child, prefix + '> ')
            md_lines.append('')
            return
        if node.name == 'img':
            alt = node.get('alt', '')
            src = node.get('src', '')
            md_lines.append(f'![{alt}]({src})')
            md_lines.append('')
            return
        if node.name == 'a':
            text = node.get_text(strip=True)
            href = node.get('href', '')
            md_lines.append(f'[{text}]({href})')
            return
        for child in node.children:
            recurse(child, prefix)

    recurse(element)
    return "\n".join(md_lines)


def main_gui():
    if tk is None:
        print("Tkinter 未安装，无法启动 GUI")
        return
    root = tk.Tk()
    root.title("Juejin 文章提取器 - GUI 默认模式")

    tk.Label(root, text="文章 URL:").grid(row=0, column=0)
    url_entry = tk.Entry(root, width=50)
    url_entry.grid(row=0, column=1)

    tk.Label(root, text="输出文件:").grid(row=1, column=0)
    out_entry = tk.Entry(root, width=50)
    out_entry.grid(row=1, column=1)
    tk.Button(root, text="浏览", command=lambda: out_entry.delete(0, tk.END) or out_entry.insert(0,
                                                                                                 filedialog.asksaveasfilename(
                                                                                                     defaultextension='.md'))).grid(
        row=1, column=2)

    def on_extract():
        url = url_entry.get().strip()
        out = out_entry.get().strip()
        if not url:
            messagebox.showwarning("输入缺失", "请填写 URL")
            return
        article = fetch_article_html(url, {'User-Agent': 'Mozilla/5.0'})
        if not article:
            return
        # 提取标题
        title_tag = article.find('h1', class_='article-title')
        title = title_tag.get_text(strip=True) if title_tag else 'article'
        # 生成默认输出文件名
        if not out:
            safe = ''.join(c for c in title if c not in r"\/:*?\"<>|'")
            out = safe + '.md'
            out_entry.delete(0, tk.END)
            out_entry.insert(0, out)
        # 转换内容
        body = article.find(id='article-root') or article
        content_md = html_to_markdown(body)
        # 在 Markdown 顶部写入标题
        md_text = f"# {title}\n\n" + content_md
        with open(out, 'w', encoding='utf-8') as f:
            f.write(md_text)
        messagebox.showinfo("完成", f"Markdown 已保存到 {out}")

    tk.Button(root, text="生成 Markdown", command=on_extract).grid(row=2, column=1)
    root.mainloop()


if __name__ == '__main__':
    # 默认启动 GUI 模式
    main_gui()
