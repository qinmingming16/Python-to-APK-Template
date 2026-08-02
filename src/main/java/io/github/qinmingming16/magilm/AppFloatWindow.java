package io.github.qinmingming16.magilm;

import android.content.Context;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.util.DisplayMetrics;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.provider.Settings;

public class AppFloatWindow {
    private static AppFloatWindow instance;
    private WindowManager mWindowManager;
    private LinearLayout mFloatView;
    private WindowManager.LayoutParams mParams;
    private Context mContext;
    // 拖动记录变量
    private float downX;
    private float downY;
    private int originX;
    private int originY;

    public static boolean canDrawOverlays(Context ctx) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            return Settings.canDrawOverlays(ctx);
        }
        return true;
    }

    // 单例初始化
    public static void init(Context context) {
        if (instance == null) {
            instance = new AppFloatWindow(context.getApplicationContext());
        }
    }

    public static AppFloatWindow getInstance() {
        return instance;
    }

    private AppFloatWindow(Context context) {
        this.mContext = context;
        this.mWindowManager = (WindowManager) context.getSystemService(Context.WINDOW_SERVICE);
        this.mParams = createLayoutParams();
        createFloatView();
        // 设置触摸拖动监听
        setFloatViewDragListener();
    }

    // 悬浮窗参数：动态适配屏幕，不再写死固定px
    private WindowManager.LayoutParams createLayoutParams() {
        WindowManager.LayoutParams params = new WindowManager.LayoutParams();
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            params.type = WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY;
        } else {
            params.type = WindowManager.LayoutParams.TYPE_PHONE;
        }
        // 移除 FLAG_NOT_TOUCHABLE，保留不抢占焦点
        params.flags = WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE;
        params.gravity = Gravity.TOP | Gravity.LEFT;
        params.x = 100;
        params.y = 300;

        // 适配多屏幕核心代码
        DisplayMetrics metrics = mContext.getResources().getDisplayMetrics();
        int screenWidthPx = metrics.widthPixels;
        // 悬浮窗宽度占屏幕宽度65%
        int floatW = (int) (screenWidthPx * 0.65f);
        // 高度按宽度比例固定
        int floatH = (int) (floatW * 0.62f);
        params.width = floatW;
        params.height = floatH;

        params.format = android.graphics.PixelFormat.RGBA_8888;
        return params;
    }

    // 创建带多按钮控件的悬浮窗布局
    private void createFloatView() {
        // 根布局：垂直排列两行按钮区域
        mFloatView = new LinearLayout(mContext);
        mFloatView.setOrientation(LinearLayout.VERTICAL);
        mFloatView.setPadding(20, 20, 20, 20);
        // 半透明灰色 ARGB(透明度,R,G,B)
        GradientDrawable bgDrawable = new GradientDrawable();
        bgDrawable.setColor(Color.argb(150, 80, 80, 80));
        bgDrawable.setCornerRadius(16);
        mFloatView.setBackground(bgDrawable);

        // 第一行：窄左按钮 + 宽中间文本 + 窄右按钮
        LinearLayout line1Layout = new LinearLayout(mContext);
        line1Layout.setOrientation(LinearLayout.HORIZONTAL);
        line1Layout.setGravity(Gravity.CENTER_VERTICAL);
        line1Layout.setLayoutParams(new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT,
                1.0f
        ));

        // 左侧按钮 权重0.6 窄
        Button btnLeft = createBaseButton("左按钮", Color.argb(200, 220, 60, 60), Color.WHITE);
        LinearLayout.LayoutParams leftLp = new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 0.6f);
        leftLp.setMargins(6, 0, 6, 0);
        btnLeft.setLayoutParams(leftLp);
        line1Layout.addView(btnLeft);

        // 中间文本 权重3 占大部分宽度
        TextView textView = new TextView(mContext);
        textView.setText("悬浮窗可拖动");
        textView.setTextSize(20);
        textView.setTextColor(Color.WHITE);
        textView.setPadding(16, 0, 16, 0);
        textView.setGravity(Gravity.CENTER);
        textView.setLayoutParams(new LinearLayout.LayoutParams(
                0, LinearLayout.LayoutParams.WRAP_CONTENT, 3.0f
        ));
        line1Layout.addView(textView);

        // 右侧按钮 权重0.6 窄
        Button btnRight = createBaseButton("右按钮", Color.argb(200, 60, 200, 80), Color.WHITE);
        LinearLayout.LayoutParams rightLp = new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 0.6f);
        rightLp.setMargins(6, 0, 6, 0);
        btnRight.setLayoutParams(rightLp);
        line1Layout.addView(btnRight);

        mFloatView.addView(line1Layout);

        // 行间距
        View spaceLine = new View(mContext);
        spaceLine.setLayoutParams(new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                16
        ));
        mFloatView.addView(spaceLine);

        // 第二行：4个并排等分按钮
        LinearLayout line2Layout = new LinearLayout(mContext);
        line2Layout.setOrientation(LinearLayout.HORIZONTAL);
        line2Layout.setGravity(Gravity.CENTER);
        line2Layout.setLayoutParams(new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT,
                1.0f
        ));

        Button btn1 = createBaseButton("按钮1", Color.argb(200, 60, 140, 220), Color.WHITE); // 蓝
        Button btn2 = createBaseButton("按钮2", Color.argb(200, 230, 160, 0), Color.BLACK); // 橙
        Button btn3 = createBaseButton("按钮3", Color.argb(200, 160, 60, 210), Color.WHITE); // 紫
        Button btn4 = createBaseButton("按钮4", Color.argb(200, 40, 180, 160), Color.BLACK); // 青

        line2Layout.addView(btn1);
        line2Layout.addView(btn2);
        line2Layout.addView(btn3);
        line2Layout.addView(btn4);

        mFloatView.addView(line2Layout);
    }

    /**
     * 通用按钮构建方法，支持自定义背景色、文字颜色
     * 新增按钮内边距，解决文字显示不全问题
     * @param text 按钮文字
     * @param bgColor 按钮背景ARGB颜色
     * @param textColor 文字颜色
     * @return Button
     */
    private Button createBaseButton(String text, int bgColor, int textColor) {
        Button btn = new Button(mContext);
        btn.setText(text);
        btn.setTextSize(14);
        btn.setTextColor(textColor);
        // 增加按钮内边距，防止文字挤压截断
        btn.setPadding(12, 10, 12, 10);
        // 按钮圆角背景
        GradientDrawable btnBg = new GradientDrawable();
        btnBg.setColor(bgColor);
        btnBg.setCornerRadius(8);
        btn.setBackground(btnBg);
        // 宽高权重均分，左右间距
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                0, LinearLayout.LayoutParams.WRAP_CONTENT, 1.0f
        );
        lp.setMargins(6, 0, 6, 0);
        btn.setLayoutParams(lp);
        return btn;
    }

    // 拖动触摸逻辑（完全未修改）
    private void setFloatViewDragListener() {
        mFloatView.setOnTouchListener(new View.OnTouchListener() {
            @Override
            public boolean onTouch(View v, MotionEvent event) {
                switch (event.getAction()) {
                    case MotionEvent.ACTION_DOWN:
                        downX = event.getRawX();
                        downY = event.getRawY();
                        originX = mParams.x;
                        originY = mParams.y;
                        break;
                    case MotionEvent.ACTION_MOVE:
                        float moveX = event.getRawX() - downX;
                        float moveY = event.getRawY() - downY;
                        mParams.x = originX + (int) moveX;
                        mParams.y = originY + (int) moveY;
                        mWindowManager.updateViewLayout(mFloatView, mParams);
                        break;
                }
                return true;
            }
        });
    }

    // 显示悬浮窗
    public static void show() {
        new Handler(Looper.getMainLooper()).post(() -> {
            try {
                AppFloatWindow self = getInstance();
                if (self == null || self.mFloatView == null) return;
                if (self.mFloatView.getParent() == null) {
                    self.mWindowManager.addView(self.mFloatView, self.mParams);
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        });
    }

    // 隐藏悬浮窗（修复括号缺失语法错误）
    public static void hide() {
        new Handler(Looper.getMainLooper()).post(() -> {
            try {
                AppFloatWindow self = getInstance();
                if (self == null || self.mFloatView == null) return;
                if (self.mFloatView.getParent() != null) {
                    self.mWindowManager.removeView(self.mFloatView);
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        });
    }
}

