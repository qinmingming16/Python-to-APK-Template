package io.github.qinmingming16.magilm;

import android.content.Context;
import android.widget.Toast;
import org.kivy.android.PythonActivity;

public class ToastTool {
    public static void show(final String message) {
        try {
            // 拿到全局上下文
            final Context ctx = PythonActivity.mActivity.getApplicationContext();

            // 关键：必须 runOnUiThread
            PythonActivity.mActivity.runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    Toast.makeText(ctx, message, Toast.LENGTH_SHORT).show();
                }
            });

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}

