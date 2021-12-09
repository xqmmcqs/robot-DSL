.. robot-DSL documentation master file, created by
   sphinx-quickstart on Wed Dec  1 18:50:11 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

robot-DSL 文档
===================

简介
====

robot-DSL定义了一个领域特定脚本语言，这个语言能够描述在线客服机器人的自动应答逻辑，并设计实现了一个解释器，可以解释执行这个脚本。该解释器可以根据用户的不同输入，根据脚本的逻辑设计给出相应的应答。

robot-DSL将输入和应答逻辑封装为Restful API以供调用，并且实现了一个有美观GUI的客户端。

模块介绍
========

.. toctree::
   :maxdepth: 2

   state_machine
   parser
   user_manage
   app
   client

用户指南
========

.. toctree::
   :maxdepth: 2

   user_guide

测试
====

.. toctree::
   :maxdepth: 2

   unittest

索引表
======

* :ref:`genindex`
* :ref:`search`
