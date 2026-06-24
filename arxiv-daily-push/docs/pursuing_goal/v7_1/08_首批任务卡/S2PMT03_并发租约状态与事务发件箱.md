# S2PMT03｜并发租约、状态与事务发件箱

实现 row_version、lease/fencing、cycle_id/M4 watermark 和 outbox。禁止声称 exactly-once；使用 at-least-once + 应用幂等。必须复现 SMTP accept 后 crash。