# If we don't need RTTI or EH, there's no reason to export anything
# from the hello plugin.
if( NOT LLVM_REQUIRES_RTTI )
  if( NOT LLVM_REQUIRES_EH )
    set(LLVM_EXPORTED_SYMBOL_FILE ${CMAKE_CURRENT_SOURCE_DIR}/HelloIR2Vec.exports)
  endif()
endif()

if(WIN32 OR CYGWIN)
  set(LLVM_LINK_COMPONENTS Core Support)
endif()

add_llvm_library(LLVMHelloIR2Vec MODULE BUILDTREE_ONLY
  Hello.cpp
  
  # LINK_COMPONENTS
  # IR2Vec

  DEPENDS
  intrinsics_gen
  PLUGIN_TOOL
  opt
  
  )




