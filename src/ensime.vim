if !has('python')
    echo "Error: +python support is required."
    finish
endif

function! LocationOfCursor()
    let pos = col('.') -1
    let line = getline('.')
    let bc = strpart(line,0,pos)
    let ac = strpart(line, pos, len(line)-pos)
    let col = getpos('.')[2]
    let linesTillC = getline(1, line('.')-1)+[getline('.')[:(col-1)]]
    return len(join(linesTillC,"\n"))
endfunction

" Assuming the Python files are in the same directory as this ensime.vim, this
" should load them correctly.
python << EOF
import vim, sys

# Where this script is located, and hopefully the Python scripts too.
VIMENSIMEPATH = vim.eval("""expand("<sfile>:p:h")""")
sys.path.append(VIMENSIMEPATH)
EOF
execute "pyfile ".fnameescape(fnamemodify(expand("<sfile>"), ":p:h")."/swank.py") 
execute "pyfile ".fnameescape(fnamemodify(expand("<sfile>"), ":p:h")."/ensime.py") 

python << EOF
# All global Python variables are defined here.
class Printer:
    def out(self, arg):
        vim.command("""echohl Normal | echomsg "Ensime: %s" """ % arg)
    def err(self, arg):
        vim.command("""echohl Error | echomsg "Ensime error: %s" """ % arg)

def cursorOffset():
    return vim.eval("""LocationOfCursor()""")
    #return vim.eval("""line2byte(line("."))+col(".")""")

def fullFileName():
    return vim.eval("""fnameescape(expand("%:p"))""")

ensimeclient = None
printer = Printer()

EOF

function! EnsimeStart()
python << EOF
try:
    currentfiledir = vim.eval("expand('%:p:h')")
    ensimeclient = EnsimeClient(printer)
    ensimeclient.connect(currentfiledir)
except RuntimeError as msg:
    printer.err(msg)
EOF
return
endfunction

function! EnsimeStop()
python << EOF
try:
    if ensimeclient is not None:
        ensimeclient.disconnect()
    else:
        printer.err("No instance running.")
except RuntimeError as msg:
    printer.err(msg) 
EOF
return
endfunction

function! TypecheckFile()
python << EOF
ensimeclient.swankSend("""(swank:typecheck-file "%s")""" % fullFileName())
EOF
endfunction

function! TypeAtPoint()
python << EOF
# offset = cursorOffset()
# printer.out("Offset : %d" % int(offset))
# printer.out("File : %s" % fullFileName())
ensimeclient.swankSend("""(swank:type-at-point "%s" %d)""" % (fullFileName(), int(cursorOffset())))
EOF
endfunction
