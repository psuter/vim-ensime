if !has('python')
    echo "Error: +python support is required."
    finish
endif

" Assuming the Python files are in the same directory as this ensime.vim, this
" should load them correctly.
python << EOF
import vim, sys

# Where this script is located, and hopefully the Python scripts too.
VIMENSIMEPATH = vim.eval("expand('<sfile>:p:h')")
sys.path.append(VIMENSIMEPATH)
EOF
execute "pyfile ".fnameescape(fnamemodify(expand("<sfile>"), ":p:h")."/swank.py") 
execute "pyfile ".fnameescape(fnamemodify(expand("<sfile>"), ":p:h")."/ensime.py") 

python << EOF
# All global Python variables are defined here.
class Printer:
    def __call__(self, arg):
        print arg

ENSIME = {
  "client" : None,
  "printer" : Printer()
}

EOF

function! EnsimeInit()
python << EOF
def pyEnsimeInit():
    try:
        currentfiledir = vim.eval("expand('%:p:h')")
        ENSIME["client"] = EnsimeClient(ENSIME["printer"])
        ENSIME["client"].connect(currentfiledir)
    except RuntimeError as msg:
        vim.command("""echoerr "%s" """ % msg)        

pyEnsimeInit()
EOF
return
endfunction

function! EnsimeInc()
python << EOF
state = state + 1
vim.current.buffer.append("%d" % state)
EOF
endfunction
