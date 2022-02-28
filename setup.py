import setuptools

with open('README.md', 'r') as rf:
    readme = rf.read()

setuptools.setup(
    name='vexptoolbox',
    version='0.1',
    description='Toolbox for Behavioral Experiments using Vizard',
    long_description=readme,
    long_description_content_type='text/markdown',
    url='https://github.com/ischtz/vizard-experiment-toolbox',
    author='Immo Schuetz',
    author_email='schuetz.immo@gmail.com',
    license='MIT',
    packages=setuptools.find_packages(),
    install_requires=[],
    zip_safe=True,
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Science/Research',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',        
        'Programming Language :: Python :: 2.7'
    ],
    options={'bdist_wheel':{'universal':'1'}}
    )

