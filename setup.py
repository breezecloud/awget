import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="awget",  # 用自己的名替换其中的YOUR_USERNAME_
    version="0.1",  # 包版本号，便于维护版本,保证每次发布都是版本都是唯一的
    author="luping",  # 作者，可以写自己的姓名
    author_email="Lucas.lu@decentinfo.com.cn",  # 作者联系方式，可写自己的邮箱地址
    description="Pure python download utility can batch download of files listed based on a certain URL",  # 包的简述
    long_description=long_description,  # 包的详细介绍，一般在README.md文件内
    long_description_content_type="text/markdown",
    url="https://github.com/breezecloud/awget",  # 自己项目地址，比如github的项目地址
    packages=setuptools.find_packages(),
    classifiers=[
        'Environment :: Console',
        'License :: Public Domain',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking',
        'Topic :: Utilities',
    ],

    py_modules=['awget'],
    python_requires='>=3.0',  # 对python的最低版本要求
)