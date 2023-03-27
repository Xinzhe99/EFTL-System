import os
import re
from PIL import Image

def config_model_dir(project_dir = os.getcwd(),resume=False,subdir_name='models'):
    # 获取当前项目目录
    # 获取models文件夹的路径
    models_dir = os.path.join(project_dir, subdir_name)
    # 如果models文件夹不存在，就创建它
    if not os.path.exists(models_dir):
        os.mkdir(models_dir)
    # 如果是第一次运行 创建models0
    if not os.path.exists(os.path.join(models_dir,subdir_name+'1')):
        os.mkdir(os.path.join(models_dir,subdir_name+'1'))
        return os.path.join(models_dir,subdir_name+'1')
    else:
        # 获取models文件夹下已有的子文件夹
        sub_dirs = [d for d in os.listdir(models_dir) if os.path.isdir(os.path.join(models_dir, d))]
        sub_dirs.sort(key=lambda l: int(re.findall('\d+', l)[0]))
        last_numbers=re.findall("\d+",sub_dirs[-1])#list
        if resume==False:
            new_sub_dir_name = subdir_name + str(int(last_numbers[0]) + 1)
        else:
            new_sub_dir_name = subdir_name + str(int(last_numbers[0]))
        model_dir_path = os.path.join(models_dir, new_sub_dir_name)
        if resume == False:
            os.mkdir(model_dir_path)
        else:
            pass
        # 把创建的路径存在model_save变量里
        return model_dir_path

def nearest_odd(n):
  if n % 2 == 0: # n是偶数
    return n + 1 # 返回较大的奇数
  else: # n是奇数
    return n # 返回n本身

#获取文件夹中图片的长宽
def get_pic_size_in_dir(folder):
    # 遍历文件夹中的所有文件
    for file in os.listdir(folder):
        # 拼接文件夹路径和文件名
        filename = os.path.join(folder, file)
        # 判断是否是图片文件
        if os.path.isfile(filename) and file.endswith((".jpg", ".png", ".bmp")):
            # 打开图片并获取尺寸
            img = Image.open(filename)
            width, height = img.size
            break
            # 返回第一张图片的宽度和高度
    return width, height


#获取文件夹中图片的类型
def get_first_image_format(folder):
    # 遍历文件夹中的所有文件
    for file in os.listdir(folder):
        # 拼接文件夹路径和文件名
        filename = os.path.join(folder, file)
        # 判断是否是图片文件
        if os.path.isfile(filename) and file.endswith((".jpg", ".png", ".bmp")):
            # 获取图片的扩展名
            ext = os.path.splitext(file)[1]
            break
            # 返回第一张图片的格式
    return ext

#判断文件类型结尾是否以xxx结尾
def judge_format(path):
    # 假设model_path是你要判断的文件路径
    # 获取文件名
    filename = os.path.basename(path)

    # 判断文件名是否以指定的后缀名结尾
    if filename.endswith((".pth", ".pt", ".ckpt")):
        # 如果是，输出"yes"
        return True
    else:
        # 如果不是，输出"no"
        return False

#批量去除文件夹里的空格和括号
import os
def rename_files(path):
    for filename in os.listdir(path):
        new_filename = filename.replace(" ", "").replace("(", "").replace(")", "")
        os.rename(os.path.join(path, filename), os.path.join(path, new_filename))

#判断文本内容是不是数字
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False