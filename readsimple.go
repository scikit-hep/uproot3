package main

import "go-hep.org/x/hep/rootio"
import "fmt"

func main() {
	f, err := rootio.Open("/home/pivarski/storage/data/TrackResonanceNtuple_compressed.root")
	obj, err2 := f.Get("twoMuon")
	tree := obj.(rootio.Tree)
	fmt.Printf("entries= %v\n", tree.Entries())

	var (
		mass_mumu float32
		px float32
		py float32
		pz float32
	)
	scanVars := []rootio.ScanVar{
		{Name: "mass_mumu", Value: &mass_mumu},
		{Name: "px", Value: &px},
		{Name: "py", Value: &py},
		{Name: "pz", Value: &pz},
	}

	sc, err3 := rootio.NewScannerVars(tree, scanVars...)

	var total float32
	sc.Next()
		err4 := sc.Scan()
		fmt.Printf("%d %v %v %v %v\n", sc.Entry(), mass_mumu, px, py, pz)
		total += mass_mumu + px + py + pz
		_ = err4

	fmt.Printf("%v\n", total)

	_ = err
	_ = err2
	_ = err3
}
