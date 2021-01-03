import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.URL;
import java.util.Calendar;
import java.util.concurrent.CountDownLatch;

/**
 * @Desc: Venus并发访问测试
 * @Author: huangzhiyuan
 * @CreateDate: 2020/11/2 9:57 下午
 * @Modify:
 * Java访问网页：https://www.cnblogs.com/weilunhui/p/3854249.html
 */

class Action implements Runnable{
    private String URI;
    private String threadName;
    private CountDownLatch countDownLatch;
    private long sum;
    private int conNum;
    public Action(String URI,CountDownLatch countDownLatch){
        this.URI = URI;
        this.countDownLatch = countDownLatch;
        this.sum = 0;
        this.conNum = 0;
    }
    public void setThreadName(String threadName){
        this.threadName = threadName;
    }
    @Override
    public void run() {
        try{
            // 构造一个URL对象
            URL turl = new URL(this.URI);
            // 连接URL，获取到字节流
            InputStream in = turl.openStream();
            // 将字节流转换城字符流
            InputStreamReader isr = new InputStreamReader(in);
            BufferedReader br = new BufferedReader(isr);
            // 读数据
            String str;
            //Calendar calendar = Calendar.getInstance();
            long beginm = System.currentTimeMillis();
            while((str = br.readLine()) != null){
                //System.out.println(str);
            }
            long endm = System.currentTimeMillis();
            System.out.println(threadName+"-打开网页用时："+(endm-beginm)+"ms");
            br.close();
            isr.close();
            in.close();
            synchronized(this) {
                this.sum += (endm-beginm);
                this.conNum++;
                System.out.println(this.conNum);
            }
        }catch (Exception e){
            e.printStackTrace();
        }
        finally {
            countDownLatch.countDown();
        }
    }

    public float avg(){
        return this.sum / this.conNum;
    }

}

public class ConcurrencyTesting {
    public static void main(String[] args) throws Exception{
        int n = 100;
        CountDownLatch countDownLatch = new CountDownLatch(n);
        Action action = new Action("INPUT YOUR TESTING URL HERE",countDownLatch);
        long beginm = System.currentTimeMillis();
        for(int i = 0 ; i < n ; i++){
            Thread t1 = new Thread(action);
            action.setThreadName(t1.getName());
            t1.start();
        }
        countDownLatch.await();
        long endm = System.currentTimeMillis();
        System.out.println("程序用时："+(endm-beginm)+"ms");
        System.out.println("平均打开网页用时："+ action.avg()+"ms");
    }
}
