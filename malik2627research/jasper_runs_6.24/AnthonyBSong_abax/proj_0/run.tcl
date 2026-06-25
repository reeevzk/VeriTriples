clear -all

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/demos /home/rk6650/VeriTriples/malik2627research/repos_6.24/AnthonyBSong_abax/demos/mv_mem.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/demos /home/rk6650/VeriTriples/malik2627research/repos_6.24/AnthonyBSong_abax/demos/add.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/demos /home/rk6650/VeriTriples/malik2627research/repos_6.24/AnthonyBSong_abax/demos/mv.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/demos /home/rk6650/VeriTriples/malik2627research/repos_6.24/AnthonyBSong_abax/demos/vvadd.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/demos /home/rk6650/VeriTriples/malik2627research/repos_6.24/AnthonyBSong_abax/demos/wsa.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/demos /home/rk6650/VeriTriples/malik2627research/repos_6.24/AnthonyBSong_abax/demos/vvadd_mem.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/demos /home/rk6650/VeriTriples/malik2627research/repos_6.24/AnthonyBSong_abax/demos/mm.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/demos /home/rk6650/VeriTriples/malik2627research/repos_6.24/AnthonyBSong_abax/demos/gemm_mem.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/demos /home/rk6650/VeriTriples/malik2627research/repos_6.24/AnthonyBSong_abax/demos/mac.v }

catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/demos /home/rk6650/VeriTriples/malik2627research/repos_6.24/AnthonyBSong_abax/demos/mv_mem.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/demos /home/rk6650/VeriTriples/malik2627research/repos_6.24/AnthonyBSong_abax/demos/mv.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/demos /home/rk6650/VeriTriples/malik2627research/repos_6.24/AnthonyBSong_abax/demos/vvadd.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/demos /home/rk6650/VeriTriples/malik2627research/repos_6.24/AnthonyBSong_abax/demos/vvadd_mem.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/demos /home/rk6650/VeriTriples/malik2627research/repos_6.24/AnthonyBSong_abax/demos/mm.v }
catch { analyze -sv -incdir /home/rk6650/VeriTriples/malik2627research -incdir /home/rk6650/VeriTriples/malik2627research/demos /home/rk6650/VeriTriples/malik2627research/repos_6.24/AnthonyBSong_abax/demos/gemm_mem.v }


            if {[catch {elaborate -top __mv__mv_0_next} err]} {
            puts "ELAB ERROR: $err"
            exit
            }
        
        clock -infer
        clock -list
        reset -list
        prove -all -time_limit 30s
        report -all -out jasper_runs_6.24/AnthonyBSong_abax/proj_0/results.rpt
report_vacuity -out jasper_runs_6.24/AnthonyBSong_abax/proj_0/vacuity.rpt
exit
