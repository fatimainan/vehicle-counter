public class Main {
    int trial(int n)
{
    if (n==0 || n==1)
        return 1;

    int sum = 0;
    for(int i=1; i<n; i++)
        sum += trial(i)*trial(n-i);
    return sum;
}
}
