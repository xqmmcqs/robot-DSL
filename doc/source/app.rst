Restful API
===========

服务端采用Flask封装了Restful API。

Flask原生支持多线程，因此服务器的其他组件只需要处理好线程互斥访问，就可以获得较好的并发性。

.. autoflask:: app:app
   :undoc-static:
