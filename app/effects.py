from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QParallelAnimationGroup,
)

from PySide6.QtWidgets import (
    QWidget,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
)

from PySide6.QtGui import QColor

# ==========================================================
# BLUE GLOW
# ==========================================================


def add_glow(widget, color="#3B82F6", blur=18, alpha=120):

    glow = QGraphicsDropShadowEffect(widget)

    glow.setBlurRadius(blur)
    glow.setOffset(0)

    c = QColor(color)
    c.setAlpha(alpha)

    glow.setColor(c)

    widget.setGraphicsEffect(glow)

    return glow


# ==========================================================
# HOVER GLOW (NO MOVEMENT)
# ==========================================================


def hover_glow(widget, glow):

    widget._glow_anim = QPropertyAnimation(glow, b"blurRadius")

    widget._glow_anim.setDuration(300)

    widget._glow_anim.setEasingCurve(QEasingCurve.InOutQuad)

    original_enter = widget.enterEvent
    original_leave = widget.leaveEvent

    def enter(event):

        widget._glow_anim.stop()

        widget._glow_anim.setStartValue(glow.blurRadius())

        widget._glow_anim.setEndValue(24)

        widget._glow_anim.start()

        if original_enter:
            original_enter(event)

    def leave(event):

        widget._glow_anim.stop()

        widget._glow_anim.setStartValue(glow.blurRadius())

        widget._glow_anim.setEndValue(18)

        widget._glow_anim.start()

        if original_leave:
            original_leave(event)

    widget.enterEvent = enter
    widget.leaveEvent = leave


# ==========================================================
# FADE IN
# ==========================================================


def fade_in(widget, duration=700):

    opacity = QGraphicsOpacityEffect(widget)

    widget.setGraphicsEffect(opacity)

    opacity.setOpacity(0)

    anim = QPropertyAnimation(opacity, b"opacity")

    anim.setDuration(duration)

    anim.setStartValue(0)

    anim.setEndValue(1)

    anim.setEasingCurve(QEasingCurve.OutCubic)

    anim.start()

    widget._fade = anim


# ==========================================================
# PULSE GLOW
# ==========================================================


def pulse_glow(glow):

    anim = QPropertyAnimation(glow, b"blurRadius")

    anim.setStartValue(10)

    anim.setEndValue(16)

    anim.setDuration(3200)

    anim.setLoopCount(-1)

    anim.setEasingCurve(QEasingCurve.InOutQuad)

    anim.start()

    glow._pulse = anim

    return anim


# ==========================================================
# FADE + GLOW
# ==========================================================


def fade_and_glow(widget):

    glow = add_glow(widget)

    fade = QGraphicsOpacityEffect(widget)

    widget.setGraphicsEffect(fade)

    fade.setOpacity(0)

    fadeAnim = QPropertyAnimation(fade, b"opacity")

    fadeAnim.setDuration(800)

    fadeAnim.setStartValue(0)

    fadeAnim.setEndValue(1)

    fadeAnim.setEasingCurve(QEasingCurve.OutCubic)

    glowAnim = QPropertyAnimation(glow, b"blurRadius")

    glowAnim.setDuration(800)

    glowAnim.setStartValue(6)

    glowAnim.setEndValue(18)

    glowAnim.setEasingCurve(QEasingCurve.OutCubic)

    group = QParallelAnimationGroup()

    group.addAnimation(fadeAnim)

    group.addAnimation(glowAnim)

    group.start()

    widget._group = group
