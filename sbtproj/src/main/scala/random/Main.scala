package random

object Main {
  def main(args : Array[String]) : Unit = {
    println(foo(args.size))
  }

  def foo(i : Int) = i + 1
}
